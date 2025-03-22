from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.responses import RedirectResponse

from backend.app.api.routes.auth_users import (
    auth_backend,
    fastapi_users,
)
from backend.app.core.config import settings
from backend.app.db.session import get_session
from backend.app.models.url import URL
from backend.app.api.schemas.url import URLCreate, URLResponse
from backend.app.services.shortener import generate_unique_short_code

router = APIRouter()

async def get_optional_current_user(request: Request) -> Optional:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    try:
        return await fastapi_users.current_user(auth_backend)(request)
    except Exception:
        return None

@router.post("/url", response_model=URLResponse, summary="Create a new shortened URL")
async def create_url(
    url_data: URLCreate,
    db: AsyncSession = Depends(get_session),
    current_user: Optional = Depends(get_optional_current_user)
):
    short_code = await generate_unique_short_code(url_data.original_url)
    created_at = datetime.now(timezone.utc)
    expires_at = None
    if settings.URL_EXPIRE_MINUTES > 0:
        expires_at = created_at + timedelta(minutes=settings.URL_EXPIRE_MINUTES)

    new_url = URL(
        short_code=short_code,
        original_url=url_data.original_url,
        created_at=created_at,
        expires_at=expires_at,
        created_by=(current_user.id if current_user else None)
    )
    db.add(new_url)
    await db.commit()
    await db.refresh(new_url)

    full_short_url = f"{settings.APP_URL}{new_url.short_code}"

    return URLResponse(
        short_code=new_url.short_code,
        short_link=full_short_url,
        original_url=new_url.original_url,
        created_at=new_url.created_at,
        expires_at=new_url.expires_at,
    )


@router.get("/{short_code}", summary="Redirect to the original URL")
async def get_url(
        short_code: str,
        db: AsyncSession = Depends(get_session),
        no_redirect: bool = False
):
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url_entry = result.scalar_one_or_none()
    if not url_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
    if url_entry.expires_at and datetime.now(timezone.utc) > url_entry.expires_at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL expired")

    if no_redirect:
        return {"redirect_url": url_entry.original_url}

    return RedirectResponse(url=url_entry.original_url)
