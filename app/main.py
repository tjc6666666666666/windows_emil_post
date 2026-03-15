"""
Email Server - 主应用入口
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import auth_router, email_router, pages_router, admin_router
from app.services.smtp_server import smtp_server
from app.services.dkim_signer import init_dkim_signer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    from sqlalchemy import select
    from app.models.config import SystemConfig

    # 启动时初始化数据库
    await init_db()

    # 初始化DKIM签名器（自动检查/生成密钥）
    dkim_signer = init_dkim_signer()

    # 从数据库获取实际配置
    async for db in get_db():
        # 获取邮件域名
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.config_key == "mail_domain")
        )
        mail_domain_config = result.scalar_one_or_none()
        mail_domain = mail_domain_config.config_value if mail_domain_config else settings.MAIL_DOMAIN

        # 获取SMTP主机名
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.config_key == "smtp_helo_hostname")
        )
        smtp_hostname_config = result.scalar_one_or_none()
        smtp_hostname = smtp_hostname_config.config_value if smtp_hostname_config else settings.SMTP_HELO_HOSTNAME
        break

    # 启动SMTP服务器（接收邮件）
    smtp_server.start()

    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动成功!")
    print(f"📧 SMTP服务器监听: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
    print(f"🔑 DKIM签名器已就绪 (域名: {mail_domain}, 选择器: {dkim_signer.DKIM_SELECTOR})")
    print(f"🌐 Web界面: http://0.0.0.0:8000")
    print(f"📌 SMTP主机名: {smtp_hostname}")
    yield
    # 关闭时清理资源
    smtp_server.stop()
    print("👋 应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 注册路由
app.include_router(auth_router)
app.include_router(email_router)
app.include_router(pages_router)
app.include_router(admin_router)


@app.get("/api/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """健康检查接口"""
    from app.services.auth import auth_service
    mail_domain = await auth_service.get_mail_domain(db)
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mail_domain": mail_domain
    }


if __name__ == "__main__":
    import sys
    import uvicorn
    # PyInstaller 打包后禁用 reload
    is_frozen = getattr(sys, 'frozen', False)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
