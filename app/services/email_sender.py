"""
邮件发送服务模块
"""
import aiodns
import aiosmtplib
from email.message import EmailMessage
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User, Email, EmailStatus
from app.schemas.email import EmailSendRequest
from app.config import settings


class EmailSenderService:
    """邮件发送服务"""
    
    def __init__(self):
        self.resolver = aiodns.DNSResolver(nameservers=settings.DNS_SERVERS)
    
    async def resolve_mx_record(self, domain: str) -> str:
        """解析MX记录"""
        try:
            result = await self.resolver.query_dns(domain, 'MX')
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
            
            # 构造邮件
            message = EmailMessage()
            message["From"] = from_addr
            message["To"] = to_addr
            message["Subject"] = subject
            message.set_content(body)
            
            # 异步发送
            await aiosmtplib.send(
                message,
                hostname=mx_server,
                port=25,
                timeout=30
            )
            return True
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
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
            message.set_content(body)
            
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER or None,
                password=settings.SMTP_PASSWORD or None,
                timeout=30
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
        await db.flush()
        
        # 发送邮件
        success = await self.send_email_direct(
            from_addr=user.email,
            to_addr=email_data.to_addr,
            subject=email_data.subject,
            body=email_data.body or ""
        )
        
        # 更新状态
        if success:
            email.status = EmailStatus.SENT
            email.sent_at = datetime.utcnow()
        else:
            email.status = EmailStatus.FAILED
        
        await db.commit()
        await db.refresh(email)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="邮件发送失败"
            )
        
        return email


# 全局实例
email_sender_service = EmailSenderService()
