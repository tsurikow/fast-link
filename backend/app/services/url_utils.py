from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from backend.app.core.config import settings
from backend.app.api.schemas.url import URLResponse
from backend.app.models.url import URL
from fastapi import HTTPException, status

def build_full_short_url(short_code: str) -> str:
    return f"{settings.APP_URL}{short_code}"

def create_url_response(url_entry: URL) -> URLResponse:
    full_short_url = build_full_short_url(url_entry.short_code)
    return URLResponse(
        short_code=url_entry.short_code,
        short_link=full_short_url,
        original_url=url_entry.original_url,
        created_at=url_entry.created_at,
        expires_at=url_entry.expires_at,
    )

async def get_url_by_shortcode(db: AsyncSession, short_code: str) -> Optional[URL]:
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    return result.scalar_one_or_none()

def check_user_ownership(url_entry: URL, current_user: Optional) -> bool:
    if current_user is None:
        return False
    return url_entry.created_by == current_user.id