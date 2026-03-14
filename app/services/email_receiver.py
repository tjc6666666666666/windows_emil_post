"""
邮件接收服务模块
"""
import aioimaplib
import email
from email.header import decode_header
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, Email, EmailStatus
from app.config import settings


class EmailReceiverService:
    """邮件接收服务"""
    
    async def connect_imap(self, username: str, password: str):
        """连接IMAP服务器"""
        client = aioimaplib.IMAP4(host=settings.IMAP_HOST, port=settings.IMAP_PORT)
        await client.wait_hello_from_server()
        await client.login(username, password)
        await client.select()
        return client
    
    def decode_email_header(self, header_value):
        """解码邮件头"""
        if not header_value:
            return ""
        
        decoded_parts = decode_header(header_value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or 'utf-8', errors='ignore'))
            else:
                result.append(part)
        return ''.join(result)
    
    async def fetch_emails(self, user: User, limit: int = 20):
        """获取用户的邮件列表"""
        try:
            client = await self.connect_imap(user.email, user.password_hash)
            
            # 搜索所有邮件
            status, messages = await client.search('ALL')
            if status != 'OK':
                return []
            
            email_ids = messages[0].split()
            emails = []
            
            # 只获取最近的N封邮件
            for email_id in email_ids[-limit:]:
                status, msg_data = await client.fetch(email_id, '(RFC822)')
                if status == 'OK':
                    email_message = email.message_from_bytes(msg_data[1])
                    
                    emails.append({
                        'id': email_id.decode(),
                        'from': self.decode_email_header(email_message.get('From')),
                        'to': self.decode_email_header(email_message.get('To')),
                        'subject': self.decode_email_header(email_message.get('Subject')),
                        'date': email_message.get('Date'),
                    })
            
            await client.logout()
            return emails
            
        except Exception as e:
            print(f"获取邮件失败: {e}")
            return []
    
    async def fetch_email_detail(self, user: User, email_id: str):
        """获取邮件详情"""
        try:
            client = await self.connect_imap(user.email, user.password_hash)
            
            status, msg_data = await client.fetch(email_id.encode(), '(RFC822)')
            if status != 'OK':
                return None
            
            email_message = email.message_from_bytes(msg_data[1])
            
            # 提取邮件正文
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        body = payload.decode('utf-8', errors='ignore')
                        break
            else:
                payload = email_message.get_payload(decode=True)
                body = payload.decode('utf-8', errors='ignore')
            
            result = {
                'id': email_id,
                'from': self.decode_email_header(email_message.get('From')),
                'to': self.decode_email_header(email_message.get('To')),
                'subject': self.decode_email_header(email_message.get('Subject')),
                'date': email_message.get('Date'),
                'body': body
            }
            
            await client.logout()
            return result
            
        except Exception as e:
            print(f"获取邮件详情失败: {e}")
            return None


# 全局实例
email_receiver_service = EmailReceiverService()
