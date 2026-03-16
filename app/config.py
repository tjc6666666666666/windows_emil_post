"""
应用配置模块
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    # 应用配置
    APP_NAME: str = "Email Server"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # 邮件服务器域名（用户注册后自动获得 username@MAIL_DOMAIN 邮箱）
    MAIL_DOMAIN: str = os.getenv("MAIL_DOMAIN", "453627.xyz")
    
    # 数据库配置（默认使用SQLite，如需PostgreSQL请设置DATABASE_URL环境变量）
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./email_server.db"
    )
    
    # JWT配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # SMTP服务器配置（用于接收邮件）
    # SMTP_BIND: 绑定地址，0.0.0.0 表示监听所有网络接口
    # SMTP_HOST: 用于连接验证的地址，使用 127.0.0.1
    SMTP_BIND: str = os.getenv("SMTP_BIND", "0.0.0.0")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "127.0.0.1")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "25"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # IMAP配置
    IMAP_HOST: str = os.getenv("IMAP_HOST", "localhost")
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", "143"))
    
    # DNS配置（用于发送邮件时解析MX记录）
    DNS_SERVERS: list = ["8.8.8.8", "114.114.114.114"]
    
    # SMTP HELO主机名（必须有有效的A记录）
    SMTP_HELO_HOSTNAME: str = os.getenv("SMTP_HELO_HOSTNAME", "mail.453627.xyz")
    
    # 附件存储配置
    ATTACHMENT_STORAGE_PATH: str = os.getenv("ATTACHMENT_STORAGE_PATH", "./attachments")
    
    class Config:
        env_file = ".env"


settings = Settings()
