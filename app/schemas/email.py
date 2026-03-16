"""
邮件相关的Pydantic模型
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from app.models.user import EmailStatus
import re


class EmailBase(BaseModel):
    """邮件基础模型"""
    to_addr: str = Field(..., description="收件人地址，多个地址用逗号分隔")
    subject: str = Field(..., min_length=1, max_length=500, description="邮件主题")
    body: Optional[str] = Field(None, description="邮件正文")
    
    @field_validator('to_addr')
    @classmethod
    def validate_email_addresses(cls, v: str) -> str:
        """验证收件人地址（支持逗号分隔的多个地址）"""
        # 分割多个地址
        addresses = [addr.strip() for addr in v.split(',') if addr.strip()]
        if not addresses:
            raise ValueError('至少需要一个收件人地址')
        
        # 验证每个地址格式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for addr in addresses:
            if not re.match(email_pattern, addr):
                raise ValueError(f'无效的邮箱地址: {addr}')
        
        return v


class EmailCreate(EmailBase):
    """创建邮件模型"""
    pass


class EmailSendRequest(EmailCreate):
    """发送邮件请求模型"""
    pass


class AttachmentResponse(BaseModel):
    """附件响应模型"""
    id: int
    filename: str
    content_type: Optional[str] = None
    file_size: int
    
    class Config:
        from_attributes = True


class EmailResponse(EmailBase):
    """邮件响应模型"""
    id: int
    from_addr: str
    status: EmailStatus
    created_at: datetime
    sent_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EmailDetailResponse(EmailResponse):
    """邮件详情响应模型"""
    html_body: Optional[str] = None
    attachments: List[AttachmentResponse] = []


class EmailListResponse(BaseModel):
    """邮件列表响应"""
    emails: list[EmailResponse]
    total: int
    page: int
    page_size: int
