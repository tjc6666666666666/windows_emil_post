"""
SMTP服务器 - 接收外部邮件
"""
import asyncio
import logging
import socket
from email import message_from_bytes
from email.utils import parseaddr
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message
from sqlalchemy import select
from app.database import async_session_maker
from app.models.user import User, Email, EmailStatus
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)


class EmailHandler:
    """邮件处理器"""
    
    async def handle_DATA(self, server, session, envelope):
        """处理接收到的邮件"""
        try:
            # 获取邮件内容
            content = envelope.content
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            # 解析邮件
            mail_from = envelope.mail_from
            rcpt_tos = envelope.rcpt_tos
            
            logger.info(f"收到邮件: FROM {mail_from} TO {rcpt_tos}")
            
            # 解析邮件头
            message = message_from_bytes(envelope.content)
            subject = message.get('Subject', '(无主题)')
            
            # 获取邮件正文
            body = ""
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')
                            break
            else:
                payload = message.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
            
            # 存储到数据库
            async with async_session_maker() as db:
                for rcpt_to in rcpt_tos:
                    # 查找收件人
                    result = await db.execute(
                        select(User).where(User.email == rcpt_to)
                    )
                    recipient = result.scalar_one_or_none()
                    
                    if recipient:
                        # 创建邮件记录
                        email = Email(
                            sender_id=recipient.id,  # 暂时用收件人ID
                            recipient_id=recipient.id,
                            from_addr=mail_from,
                            to_addr=rcpt_to,
                            subject=subject,
                            body=body,
                            status=EmailStatus.RECEIVED,
                            created_at=datetime.utcnow()
                        )
                        db.add(email)
                        logger.info(f"邮件已保存: {subject} -> {rcpt_to}")
                    else:
                        logger.warning(f"收件人不存在: {rcpt_to}")
                
                await db.commit()
            
            return '250 Message accepted for delivery'
            
        except Exception as e:
            logger.error(f"处理邮件失败: {e}")
            import traceback
            traceback.print_exc()
            return '550 Message rejected'


class CustomController(Controller):
    """自定义Controller，解决Windows下绑定0.0.0.0的问题"""
    
    def _trigger_server(self):
        """重写验证逻辑，使用127.0.0.1连接验证"""
        # 使用 SMTP_HOST (127.0.0.1) 进行连接验证，而不是 SMTP_BIND (0.0.0.0)
        import contextlib
        try:
            with contextlib.ExitStack() as stk:
                s = stk.enter_context(
                    socket.create_connection((settings.SMTP_HOST, self.port), 1.0)
                )
                # 服务器已就绪
        except Exception:
            raise


class SMTPServerController:
    """SMTP服务器控制器"""
    
    def __init__(self):
        self.controller = None
    
    def start(self):
        """启动SMTP服务器"""
        handler = EmailHandler()
        # 使用 SMTP_BIND (0.0.0.0) 绑定所有接口
        self.controller = CustomController(
            handler,
            hostname=settings.SMTP_BIND,
            port=settings.SMTP_PORT
        )
        self.controller.start()
        logger.info(f"SMTP服务器已启动: {settings.SMTP_BIND}:{settings.SMTP_PORT}")
    
    def stop(self):
        """停止SMTP服务器"""
        if self.controller:
            self.controller.stop()
            logger.info("SMTP服务器已停止")


# 全局实例
smtp_server = SMTPServerController()
