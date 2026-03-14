"""
邮件相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.database import get_db
from app.schemas.email import EmailSendRequest, EmailResponse, EmailListResponse
from app.services.email_sender import email_sender_service
from app.api.auth import get_current_user
from app.models.user import User, Email, EmailStatus


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
    count_query = select(func.count(Email.id)).where(
        Email.sender_id == current_user.id,
        Email.status == EmailStatus.SENT
    )
    total = (await db.execute(count_query)).scalar()
    
    # 分页查询
    offset = (page - 1) * page_size
    query = (
        select(Email)
        .where(Email.sender_id == current_user.id, Email.status == EmailStatus.SENT)
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取收件箱邮件（从数据库）"""
    # 查询接收到的邮件
    query = (
        select(Email)
        .where(Email.recipient_id == current_user.id, Email.status == EmailStatus.RECEIVED)
        .order_by(Email.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    emails = result.scalars().all()
    
    # 格式化返回数据
    email_list = []
    for email in emails:
        email_list.append({
            "id": str(email.id),
            "from": email.from_addr,
            "to": email.to_addr,
            "subject": email.subject,
            "date": email.created_at.isoformat(),
        })
    
    return {"emails": email_list}


@router.get("/inbox/{email_id}")
async def get_email_detail(
    email_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取邮件详情"""
    # 查询邮件
    query = select(Email).where(
        Email.id == email_id,
        Email.recipient_id == current_user.id,
        Email.status == EmailStatus.RECEIVED
    )
    result = await db.execute(query)
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮件不存在"
        )
    
    return {
        "id": str(email.id),
        "from": email.from_addr,
        "to": email.to_addr,
        "subject": email.subject,
        "date": email.created_at.isoformat(),
        "body": email.body
    }
