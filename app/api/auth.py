"""
认证相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token, PasswordChange, AdminUserCreate
from app.services.auth import auth_service
from app.models.user import User


router = APIRouter(prefix="/api/auth", tags=["认证"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def build_user_response(user: User, db: AsyncSession) -> UserResponse:
    """构造用户响应（包含动态生成的邮箱）"""
    mail_domain = await auth_service.get_mail_domain(db)
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.get_email(mail_domain),
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户（依赖注入）"""
    payload = auth_service.decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据"
        )

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    return user


async def get_current_admin(
    current_user = Depends(get_current_user)
):
    """获取当前管理员（依赖注入）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    # 检查是否是第一个用户，自动成为管理员
    result = await db.execute(select(func.count(User.id)))
    user_count = result.scalar()
    is_first_user = (user_count == 0)

    # 非第一个用户需要检查注册开关
    if not is_first_user:
        from app.models.config import SystemConfig
        config_result = await db.execute(
            select(SystemConfig).where(SystemConfig.config_key == "allow_registration")
        )
        config = config_result.scalar_one_or_none()
        if config and config.config_value.lower() == "false":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="系统已禁止新用户注册"
            )

    user = await auth_service.register_user(db, user_data, is_admin=is_first_user)
    return await build_user_response(user, db)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_user_info(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户信息"""
    return await build_user_response(current_user, db)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    # 验证旧密码
    if not auth_service.verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )

    # 更新密码
    current_user.password_hash = auth_service.get_password_hash(password_data.new_password)
    await db.commit()

    return {"message": "密码修改成功"}


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表（仅管理员）"""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [await build_user_response(u, db) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminUserCreate,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建用户（仅管理员）"""
    # 检查用户名是否存在
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    user = User(
        username=user_data.username,
        password_hash=auth_service.get_password_hash(user_data.password),
        is_admin=user_data.is_admin
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await build_user_response(user, db)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除用户（仅管理员）"""
    # 不能删除自己
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    await db.delete(user)
    await db.commit()

    return {"message": "用户已删除"}


@router.put("/users/{user_id}/toggle-admin")
async def toggle_admin(
    user_id: int,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """切换用户管理员权限（仅管理员）"""
    # 不能修改自己的管理员权限
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的管理员权限"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    user.is_admin = not user.is_admin
    await db.commit()

    return {"message": f"用户管理员权限已{'授予' if user.is_admin else '撤销'}", "is_admin": user.is_admin}
