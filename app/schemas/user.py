"""
用户相关的Pydantic模型
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")


class UserCreate(UserBase):
    """用户注册模型（邮箱自动生成为 username@MAIL_DOMAIN）"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str  # 动态生成: username@MAIL_DOMAIN
    is_active: bool
    is_admin: bool
    created_at: datetime


class PasswordChange(BaseModel):
    """修改密码模型"""
    old_password: str = Field(..., min_length=6, description="原密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class AdminUserCreate(BaseModel):
    """管理员创建用户模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    is_admin: bool = Field(default=False, description="是否为管理员")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v


class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token数据模型"""
    username: Optional[str] = None
