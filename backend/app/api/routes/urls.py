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
from backend.app.db.session import get_async_session
from backend.app.models.url import URL
from backend.app.api.schemas.url import URLCreate, URLResponse
from backend.app.services.shortener import generate_unique_short_code
from backend.app.services.cache import get_cache, store_short_code

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
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional = Depends(get_optional_current_user)
):
    # Check if the URL already exists
    result = await db.execute(
        select(URL).where(URL.original_url == url_data.original_url).limit(1)
    )
    existing_url = result.scalar_one_or_none()

    created_at = datetime.now(timezone.utc)
    expires_at = None
    if settings.URL_EXPIRE_MINUTES > 0:
        expires_at = created_at + timedelta(minutes=settings.URL_EXPIRE_MINUTES)

    if existing_url:
        # Update expiration date
        existing_url.expires_at = expires_at
        # If user is authenticated, add them to the URL's users relationship if not already present
        if current_user and current_user not in existing_url.users:
            existing_url.users.append(current_user)
        db.add(existing_url)
        await db.commit()
        await db.refresh(existing_url)
        short_code = existing_url.short_code
        full_short_url = f"{settings.APP_URL}{short_code}"
        return URLResponse(
            short_code=short_code,
            short_link=full_short_url,
            original_url=existing_url.original_url,
            created_at=existing_url.created_at,
            expires_at=existing_url.expires_at,
        )

    # Otherwise, create a new URL record
    short_code = await generate_unique_short_code(url_data.original_url)
    new_url = URL(
        short_code=short_code,
        original_url=url_data.original_url,
        created_at=created_at,
        expires_at=expires_at,
    )
    # If the user is authenticated, add them to the relationship
    if current_user:
        new_url.users.append(current_user)
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
        db: Optional = Depends(get_async_session),
        no_redirect: bool = False
):
    # First, check in Redis cache
    cached_original_url = await get_cache(short_code)
    if cached_original_url:
        # Cache hit: Optionally update expiration in DB if needed
        try:
            result = await db.execute(select(URL).where(URL.short_code == short_code))
            url_entry = result.scalar_one_or_none()
            if url_entry:
                new_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.URL_EXPIRE_MINUTES)
                url_entry.expires_at = new_expires_at
                db.add(url_entry)
                await db.commit()
                await db.refresh(url_entry)
        except Exception as e:
            # If any error occurs updating DB, log it but continue with cached value.
            pass

        if no_redirect:
            return {"redirect_url": cached_original_url}
        return RedirectResponse(url=cached_original_url)

    # Cache miss: Query the database.
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url_entry = result.scalar_one_or_none()
    if not url_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
    if url_entry.expires_at and datetime.now(timezone.utc) > url_entry.expires_at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL expired")

    # Refresh expiration date in DB.
    new_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.URL_EXPIRE_MINUTES)
    url_entry.expires_at = new_expires_at
    db.add(url_entry)
    await db.commit()
    await db.refresh(url_entry)

    # Cache the original URL in Redis.
    await store_short_code(short_code, url_entry.original_url)

    if no_redirect:
        return {"redirect_url": url_entry.original_url}
    return RedirectResponse(url=url_entry.original_url)
