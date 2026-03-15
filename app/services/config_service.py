"""
系统配置服务
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.config import SystemConfig
from app.config import settings


class ConfigService:
    """系统配置服务"""

    _cache: dict = {}

    async def get_config(self, db: AsyncSession, key: str, default: Optional[str] = None) -> str:
        """获取配置值（优先从缓存读取）"""
        if key in self._cache:
            return self._cache[key]

        result = await db.execute(
            select(SystemConfig).where(SystemConfig.config_key == key)
        )
        config = result.scalar_one_or_none()

        value = config.config_value if config else default
        if value is None:
            value = getattr(settings, key.upper(), "")

        self._cache[key] = value
        return value

    async def set_config(self, db: AsyncSession, key: str, value: str, description: str = "") -> None:
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
        self._cache[key] = value

    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()


config_service = ConfigService()
