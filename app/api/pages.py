"""
页面路由（前端HTML）
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.api.auth import get_current_user
from app.models.user import User


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
async def dashboard_page(request: Request, current_user: User = Depends(get_current_user)):
    """控制面板页面"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user
    })


@router.get("/compose", response_class=HTMLResponse)
async def compose_page(request: Request, current_user: User = Depends(get_current_user)):
    """写邮件页面"""
    return templates.TemplateResponse("compose.html", {
        "request": request,
        "user": current_user
    })


@router.get("/inbox", response_class=HTMLResponse)
async def inbox_page(request: Request, current_user: User = Depends(get_current_user)):
    """收件箱页面"""
    return templates.TemplateResponse("inbox.html", {
        "request": request,
        "user": current_user
    })
