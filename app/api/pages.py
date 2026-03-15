"""
页面路由（前端HTML）
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(tags=["页面"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """注册页面"""
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """控制面板页面"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/compose", response_class=HTMLResponse)
async def compose_page(request: Request):
    """写邮件页面"""
    return templates.TemplateResponse("compose.html", {"request": request})


@router.get("/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request):
    """收件箱页面"""
    return templates.TemplateResponse("inbox.html", {"request": request})


@router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    """初始化设置页面"""
    return templates.TemplateResponse("setup.html", {"request": request})


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """管理员页面"""
    return templates.TemplateResponse("admin.html", {"request": request})


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """个人资料页面"""
    return templates.TemplateResponse("profile.html", {"request": request})
