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
    
    # 数据库配置（默认使用SQLite，如需PostgreSQL请设置DATABASE_URL环境变量）
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./email_server.db"
    )
    
    # JWT配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # 邮件服务器配置
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "25"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # IMAP配置
    IMAP_HOST: str = os.getenv("IMAP_HOST", "localhost")
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", "143"))
    
    # DNS配置
    DNS_SERVERS: list = ["8.8.8.8", "114.114.114.114"]
    
    class Config:
        env_file = ".env"


settings = Settings()
