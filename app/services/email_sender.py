"""
邮件发送服务模块
"""
import aiodns
import aiosmtplib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User, Email, EmailStatus
from app.schemas.email import EmailSendRequest
from app.config import settings


class EmailSenderService:
    """邮件发送服务"""
    
    async def resolve_mx_record(self, domain: str) -> str:
        """解析MX记录"""
        try:
            # 在异步函数内部创建resolver，避免事件循环冲突
            resolver = aiodns.DNSResolver(nameservers=settings.DNS_SERVERS)
            result = await resolver.query_dns(domain, 'MX')
            mx_list = sorted(result.answer, key=lambda x: x.data.priority)
            return str(mx_list[0].data.exchange)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无法解析邮件服务器: {str(e)}"
            )
    
    async def send_email_direct(
        self, 
        from_addr: str, 
        to_addr: str, 
        subject: str, 
        body: str
    ) -> bool:
        """直接发送邮件（通过MX记录）"""
        try:
            # 解析收件人域名的MX记录
            target_domain = to_addr.split('@')[1]
            mx_server = await self.resolve_mx_record(target_domain)
            print(f"解析到MX服务器: {mx_server}")
            
            # 构造邮件
            message = EmailMessage()
            message["From"] = from_addr
            message["To"] = to_addr
            message["Subject"] = subject
            message["Date"] = formatdate(localtime=True)
            message["Message-ID"] = make_msgid(domain=settings.MAIL_DOMAIN)
            message.set_content(body)
            
            # 异步发送（参考原email_sender.py的实现）
            print(f"正在连接 {mx_server}:25 并发送邮件...")
            async with aiosmtplib.SMTP(
                hostname=mx_server, 
                port=25, 
                timeout=30,
                use_tls=False,  # 25端口通常不使用TLS
                local_hostname=settings.SMTP_HELO_HOSTNAME  # 设置有效的HELO主机名
            ) as smtp:
                # 尝试STARTTLS（如果服务器支持）
                try:
                    await smtp.starttls()
                except Exception:
                    pass  # 如果不支持STARTTLS，继续使用明文
                
                await smtp.send_message(message)
            
            print("邮件发送成功！")
            return True
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def send_email_via_smtp(
        self, 
        from_addr: str, 
        to_addr: str, 
        subject: str, 
        body: str
    ) -> bool:
        """通过SMTP服务器发送邮件"""
        try:
            message = EmailMessage()
            message["From"] = from_addr
            message["To"] = to_addr
            message["Subject"] = subject
            message["Date"] = formatdate(localtime=True)
            message["Message-ID"] = make_msgid(domain=settings.MAIL_DOMAIN)
            message.set_content(body)
            
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER or None,
                password=settings.SMTP_PASSWORD or None,
                timeout=30,
                local_hostname=settings.SMTP_HELO_HOSTNAME  # 设置有效的HELO主机名
            )
            return True
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    async def send_email(
        self, 
        db: AsyncSession, 
        user: User, 
        email_data: EmailSendRequest
    ) -> Email:
        """发送邮件"""
        # 创建邮件记录
        email = Email(
            sender_id=user.id,
            from_addr=user.email,
            to_addr=email_data.to_addr,
            subject=email_data.subject,
            body=email_data.body or "",
            status=EmailStatus.DRAFT
        )
        db.add(email)
        await db.commit()  # 先提交，避免长时间锁定
        await db.refresh(email)
        
        # 发送邮件（不持有数据库锁）
        try:
            success = await self.send_email_direct(
                from_addr=user.email,
                to_addr=email_data.to_addr,
                subject=email_data.subject,
                body=email_data.body or ""
            )
        except Exception as e:
            print(f"邮件发送异常: {e}")
            success = False
        
        # 更新状态（新的数据库会话）
        if success:
            email.status = EmailStatus.SENT
            email.sent_at = datetime.utcnow()
        else:
            email.status = EmailStatus.FAILED
        
        db.add(email)
        await db.commit()
        await db.refresh(email)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="邮件发送失败，请检查收件人地址是否正确"
            )
        
        return email


# 全局实例
email_sender_service = EmailSenderService()
