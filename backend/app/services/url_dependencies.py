from fastapi import Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_async_session
from backend.app.models.url import URL
from backend.app.api.routes.auth_users import fastapi_users, auth_backend

async def get_user_owned_url(
    short_code: str,
    db: AsyncSession = Depends(get_async_session),
    current_user = Depends(fastapi_users.current_user(auth_backend))
) -> URL:
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url_entry = result.scalar_one_or_none()
    if not url_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
    if url_entry.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this URL")
    return url_entry