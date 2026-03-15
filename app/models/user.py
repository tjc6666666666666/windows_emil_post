"""
用户和邮件数据模型
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class EmailStatus(str, enum.Enum):
    """邮件状态"""
    DRAFT = "draft"          # 草稿
    SENT = "sent"            # 已发送
    RECEIVED = "received"    # 已接收
    FAILED = "failed"        # 发送失败


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    # email 由 username + 当前域名动态生成，不存储在数据库中
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    sent_emails: Mapped[list["Email"]] = relationship(
        "Email", back_populates="sender", foreign_keys="Email.sender_id"
    )
    received_emails: Mapped[list["Email"]] = relationship(
        "Email", back_populates="recipient", foreign_keys="Email.recipient_id"
    )

    def get_email(self, mail_domain: str) -> str:
        """根据域名动态生成邮箱地址"""
        return f"{self.username}@{mail_domain}"

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Email(Base):
    """邮件模型"""
    __tablename__ = "emails"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # 邮件基本信息
    from_addr: Mapped[str] = mapped_column(String(255), nullable=False)
    to_addr: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=True)
    
    # 邮件状态
    status: Mapped[EmailStatus] = mapped_column(
        SQLEnum(EmailStatus), 
        default=EmailStatus.DRAFT,
        nullable=False
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # 关联关系
    sender: Mapped["User"] = relationship("User", back_populates="sent_emails", foreign_keys=[sender_id])
    recipient: Mapped["User"] = relationship("User", back_populates="received_emails", foreign_keys=[recipient_id])
    
    def __repr__(self):
        return f"<Email(id={self.id}, from={self.from_addr}, to={self.to_addr}, subject={self.subject})>"
