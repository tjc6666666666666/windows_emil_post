"""
SMTP服务器 - 接收外部邮件
"""
import asyncio
import logging
import socket
from email import message_from_bytes
from email.utils import parseaddr
from email.header import decode_header
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message
from sqlalchemy import select
from app.database import async_session_maker
from app.models.user import User, Email, EmailStatus, Attachment
from datetime import datetime
from app.config import settings
from app.services.attachment_storage import attachment_storage

logger = logging.getLogger(__name__)


def decode_email_header(header_value: str, default: str = '(无主题)') -> str:
    """解码 RFC 2047 编码的邮件头（支持多段编码）"""
    if not header_value:
        return default
    
    try:
        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                decoded_parts.append(part)
        return ''.join(decoded_parts)
    except Exception as e:
        logger.warning(f"解码邮件头失败: {e}, 原始值: {header_value}")
        return header_value


def decode_payload(payload: bytes, charset: str = None) -> str:
    """解码邮件正文，支持多种编码"""
    if not payload:
        return ""
    
    # 尝试多种编码
    encodings = []
    if charset:
        encodings.append(charset)
    encodings.extend(['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'iso-8859-1'])
    
    for encoding in encodings:
        try:
            return payload.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    
    # 最后使用 ignore 模式
    return payload.decode('utf-8', errors='ignore')


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
            subject = decode_email_header(message.get('Subject'), '(无主题)')
            
            # 获取邮件正文和附件
            body = ""
            html_body = ""
            attachments_data = []
            
            if message.is_multipart():
                for part in message.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get("Content-Disposition", "")
                    filename = part.get_filename()
                    
                    # 解码文件名（处理编码的文件名）
                    if filename:
                        filename = decode_email_header(filename, filename)
                    
                    # 检测是否为附件（更完善的检测逻辑）
                    is_attachment = False
                    
                    # 1. Content-Disposition 明确标记为 attachment
                    if "attachment" in content_disposition.lower():
                        is_attachment = True
                    # 2. 有文件名且不是正文类型（排除 text/plain 和 text/html 作为内联内容）
                    elif filename and content_type not in ("text/plain", "text/html"):
                        is_attachment = True
                    # 3. 有文件名且 Content-Disposition 为 inline，但不是正文
                    elif filename and "inline" in content_disposition.lower() and content_type not in ("text/plain", "text/html"):
                        is_attachment = True
                    
                    if is_attachment and filename:
                        payload = part.get_payload(decode=True)
                        if payload:
                            attachments_data.append({
                                'filename': filename,
                                'content': payload,
                                'content_type': content_type
                            })
                            logger.info(f"发现附件: {filename}, 类型: {content_type}, 大小: {len(payload)} 字节")
                    else:
                        # 提取正文内容（只处理 text/plain 和 text/html）
                        if content_type in ("text/plain", "text/html") and not filename:
                            payload = part.get_payload(decode=True)
                            if payload:
                                # 获取字符集
                                charset = part.get_content_charset()
                                decoded = decode_payload(payload, charset)
                                if content_type == "text/plain" and not body:
                                    body = decoded
                                elif content_type == "text/html" and not html_body:
                                    html_body = decoded
            else:
                payload = message.get_payload(decode=True)
                if payload:
                    charset = message.get_content_charset()
                    body = decode_payload(payload, charset)
            
            # 存储到数据库
            async with async_session_maker() as db:
                for rcpt_to in rcpt_tos:
                    # 从邮箱地址解析用户名（格式：username@domain）
                    if '@' in rcpt_to:
                        username = rcpt_to.split('@')[0]
                    else:
                        username = rcpt_to

                    # 查找收件人（根据用户名）
                    result = await db.execute(
                        select(User).where(User.username == username)
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
                            html_body=html_body,
                            status=EmailStatus.RECEIVED,
                            created_at=datetime.utcnow()
                        )
                        db.add(email)
                        await db.flush()  # 获取email.id
                        
                        # 保存附件
                        for att_data in attachments_data:
                            # 使用附件存储服务保存文件
                            stored_filename, file_path, relative_path = attachment_storage.save(
                                att_data['content'],
                                att_data['filename']
                            )
                            
                            # 创建附件记录
                            attachment = Attachment(
                                email_id=email.id,
                                filename=att_data['filename'],
                                stored_filename=stored_filename,
                                file_path=file_path,
                                content_type=att_data['content_type'],
                                file_size=len(att_data['content'])
                            )
                            db.add(attachment)
                            logger.info(f"附件已保存: {att_data['filename']} -> {stored_filename}")
                        
                        logger.info(f"邮件已保存: {subject} -> {rcpt_to}, 附件数: {len(attachments_data)}")
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
