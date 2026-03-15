"""
认证服务模块
"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.models.user import User
from app.models.config import SystemConfig
from app.schemas.user import UserCreate
from app.config import settings


class AuthService:
    """认证服务"""

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    def create_access_token(self, data: dict) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    def decode_token(self, token: str) -> dict:
        """解码令牌"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_mail_domain(self, db: AsyncSession) -> str:
        """获取邮件域名（优先从数据库获取）"""
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.config_key == "mail_domain")
        )
        config = result.scalar_one_or_none()
        return config.config_value if config else settings.MAIL_DOMAIN

    async def register_user(self, db: AsyncSession, user_data: UserCreate, is_admin: bool = False) -> User:
        """注册新用户（自动分配系统邮箱）"""
        # 检查用户名是否存在
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

        # 获取邮件域名
        mail_domain = await self.get_mail_domain(db)

        # 创建用户（email 由 username + domain 动态生成，不存储）
        user = User(
            username=user_data.username,
            password_hash=self.get_password_hash(user_data.password),
            is_admin=is_admin
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def authenticate_user(self, db: AsyncSession, username: str, password: str) -> User:
        """验证用户"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        if not self.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账号已被禁用"
            )

        return user


# 全局实例
auth_service = AuthService()
