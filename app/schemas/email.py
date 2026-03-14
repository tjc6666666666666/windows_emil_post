"""
邮件相关的Pydantic模型
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.user import EmailStatus


class EmailBase(BaseModel):
    """邮件基础模型"""
    to_addr: EmailStr = Field(..., description="收件人地址")
    subject: str = Field(..., min_length=1, max_length=500, description="邮件主题")
    body: Optional[str] = Field(None, description="邮件正文")


class EmailCreate(EmailBase):
    """创建邮件模型"""
    pass


class EmailSendRequest(EmailCreate):
    """发送邮件请求模型"""
    pass


class EmailResponse(EmailBase):
    """邮件响应模型"""
    id: int
    from_addr: str
    status: EmailStatus
    created_at: datetime
    sent_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EmailListResponse(BaseModel):
    """邮件列表响应"""
    emails: list[EmailResponse]
    total: int
    page: int
    page_size: int
