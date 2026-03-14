from app.api.auth import router as auth_router
from app.api.email import router as email_router
from app.api.pages import router as pages_router

__all__ = ["auth_router", "email_router", "pages_router"]
