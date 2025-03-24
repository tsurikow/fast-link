from typing import Optional

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.api.schemas.url import URLResponse, URLListResponse
from backend.app.models.url import URL

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
def create_url_list_response(url) -> URLListResponse:
    return URLListResponse(
        short_code=url.short_code,
        original_url=url.original_url,
        created_at=url.created_at,
        expires_at=url.expires_at,
        hit_count=url.hit_count,
        last_used_at=url.last_used_at,
        fixed_expiration=url.fixed_expiration,
        moved_at=getattr(url, "moved_at", None)
    )

async def get_url_by_shortcode(db: AsyncSession, short_code: str) -> Optional[URL]:
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    return result.scalar_one_or_none()

def check_user_ownership(url_entry: URL, current_user: Optional) -> bool:
    if current_user is None:
        return False
    return url_entry.created_by == current_user.id