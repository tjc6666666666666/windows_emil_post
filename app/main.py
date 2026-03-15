"""
Email Server - 主应用入口
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api import auth_router, email_router, pages_router
from app.services.smtp_server import smtp_server
from app.services.dkim_signer import init_dkim_signer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    
    # 初始化DKIM签名器（自动检查/生成密钥）
    dkim_signer = init_dkim_signer()
    
    # 启动SMTP服务器（接收邮件）
    smtp_server.start()
    
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动成功!")
    print(f"📧 SMTP服务器监听: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
    print(f"🔑 DKIM签名器已就绪 (域名: {settings.MAIL_DOMAIN}, 选择器: {dkim_signer.DKIM_SELECTOR})")
    print(f"🌐 Web界面: http://0.0.0.0:8000")
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


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mail_domain": settings.MAIL_DOMAIN
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
