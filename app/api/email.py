"""
邮件相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.schemas.email import EmailSendRequest, EmailResponse, EmailListResponse
from app.services.email_sender import email_sender_service
from app.services.email_receiver import email_receiver_service
from app.api.auth import get_current_user
from app.models.user import User, Email


router = APIRouter(prefix="/api/email", tags=["邮件"])


@router.post("/send", response_model=EmailResponse, status_code=status.HTTP_201_CREATED)
async def send_email(
    email_data: EmailSendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发送邮件"""
    email = await email_sender_service.send_email(db, current_user, email_data)
    return email


@router.get("/sent", response_model=EmailListResponse)
async def get_sent_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取已发送邮件列表"""
    # 查询总数
    count_query = select(func.count(Email.id)).where(Email.sender_id == current_user.id)
    total = (await db.execute(count_query)).scalar()
    
    # 分页查询
    offset = (page - 1) * page_size
    query = (
        select(Email)
        .where(Email.sender_id == current_user.id)
        .order_by(Email.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    emails = result.scalars().all()
    
    return EmailListResponse(
        emails=[EmailResponse.model_validate(e) for e in emails],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/inbox")
async def get_inbox_emails(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """获取收件箱邮件（从IMAP服务器）"""
    emails = await email_receiver_service.fetch_emails(current_user, limit)
    return {"emails": emails}


@router.get("/inbox/{email_id}")
async def get_email_detail(
    email_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取邮件详情"""
    email = await email_receiver_service.fetch_email_detail(current_user, email_id)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮件不存在"
        )
    return email
