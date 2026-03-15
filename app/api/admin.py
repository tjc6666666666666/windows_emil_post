"""
管理员相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.config import SystemConfig
from app.api.auth import get_current_admin
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/admin", tags=["管理员"])


class ConfigUpdate(BaseModel):
    """配置更新模型"""
    mail_domain: str = Field(..., description="邮件域名")
    smtp_helo_hostname: str = Field(..., description="SMTP HELO主机名")
    allow_registration: bool = Field(default=True, description="允许新用户注册")


class ConfigResponse(BaseModel):
    """配置响应模型"""
    mail_domain: str
    smtp_helo_hostname: str
    allow_registration: bool


async def get_config_value(db: AsyncSession, key: str, default: str = "") -> str:
    """获取配置值"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == key)
    )
    config = result.scalar_one_or_none()
    return config.config_value if config else default


async def set_config_value(db: AsyncSession, key: str, value: str, description: str = ""):
    """设置配置值"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == key)
    )
    config = result.scalar_one_or_none()

    if config:
        config.config_value = value
    else:
        config = SystemConfig(
            config_key=key,
            config_value=value,
            description=description
        )
        db.add(config)

    await db.commit()


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取系统配置（仅管理员）"""
    from app.config import settings

    mail_domain = await get_config_value(db, "mail_domain", settings.MAIL_DOMAIN)
    smtp_helo_hostname = await get_config_value(db, "smtp_helo_hostname", settings.SMTP_HELO_HOSTNAME)
    allow_registration = await get_config_value(db, "allow_registration", "true")

    return ConfigResponse(
        mail_domain=mail_domain,
        smtp_helo_hostname=smtp_helo_hostname,
        allow_registration=allow_registration.lower() == "true"
    )


@router.put("/config", response_model=ConfigResponse)
async def update_config(
    config_data: ConfigUpdate,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新系统配置（仅管理员）"""
    await set_config_value(db, "mail_domain", config_data.mail_domain, "邮件域名")
    await set_config_value(db, "smtp_helo_hostname", config_data.smtp_helo_hostname, "SMTP HELO主机名")
    await set_config_value(db, "allow_registration", str(config_data.allow_registration).lower(), "允许注册")

    return config_data


@router.get("/check-init")
async def check_init(db: AsyncSession = Depends(get_db)):
    """检查系统是否已初始化"""
    from app.models.user import User

    result = await db.execute(select(User))
    users = result.scalars().all()

    # 获取注册开关状态
    allow_registration = await get_config_value(db, "allow_registration", "true")

    return {
        "initialized": len(users) > 0,
        "user_count": len(users),
        "allow_registration": allow_registration.lower() == "true"
    }


@router.get("/dns-config")
async def get_dns_config(
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取DNS配置信息（仅管理员）"""
    from app.services.dkim_signer import get_dkim_signer
    from app.config import settings

    # 获取域名配置
    mail_domain = await get_config_value(db, "mail_domain", settings.MAIL_DOMAIN)
    smtp_hostname = await get_config_value(db, "smtp_helo_hostname", settings.SMTP_HELO_HOSTNAME)

    # 获取DKIM公钥记录
    dkim_signer = get_dkim_signer()
    dkim_record = dkim_signer.get_public_key_dns_record()
    dkim_selector = dkim_signer.DKIM_SELECTOR

    return {
        "mail_domain": mail_domain,
        "smtp_hostname": smtp_hostname,
        "dkim_selector": dkim_selector,
        "dkim_record": dkim_record
    }
