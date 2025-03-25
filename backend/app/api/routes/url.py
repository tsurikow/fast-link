from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from backend.app.core.security import current_active_user
from backend.app.models.user import User
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from backend.app.core.config import settings
from backend.app.db.session import get_async_session
from backend.app.models.url import URL, ExpiredURL
from backend.app.api.schemas.url import URLCreate, URLResponse, URLCustomCreate, URLUpdateRequest, URLListResponse
from backend.app.services.shortener import generate_unique_short_code
from backend.app.services.cache import get_cache, store_short_code, delete_cache
from backend.app.services.url_helpers import update_url_background
from backend.app.services.url_utils import (
    create_url_response,
    get_url_by_shortcode,
    create_url_list_response
)
from backend.app.services.url_dependencies import get_user_owned_url

router = APIRouter(tags=["urls"])


@router.post("/url", response_model=URLResponse, summary="Create a new shortened URL")
async def create_url(
        url_data: URLCreate,
        db: AsyncSession = Depends(get_async_session),
        current_user: Optional[User] = Depends(current_active_user)
):

    if current_user:
        result = await db.execute(
            select(URL).where(
                URL.original_url == url_data.original_url,
                URL.created_by == current_user.id
            ).limit(1)
        )
        existing_url = result.scalar_one_or_none()
        if existing_url:
            new_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.URL_EXPIRE_MINUTES)
            existing_url.expires_at = new_expires_at
            db.add(existing_url)
            await db.commit()
            await db.refresh(existing_url)
            return create_url_response(existing_url)

    short_code = await generate_unique_short_code(url_data.original_url)
    new_url = URL(
        short_code=short_code,
        original_url=url_data.original_url,
        created_at=datetime.now(timezone.utc),
        expires_at=(datetime.now(timezone.utc) + timedelta(minutes=settings.URL_EXPIRE_MINUTES)
                    if settings.URL_EXPIRE_MINUTES > 0 else None),
        created_by=(current_user.id if current_user else None)
    )
    db.add(new_url)
    await db.commit()
    await db.refresh(new_url)
    return create_url_response(new_url)


@router.get("/my_urls", summary="Get URLs created by the authenticated user", response_model=List[URLListResponse])
async def get_my_urls(
    url_type: str = Query("active", description="Type of URLs to fetch: 'active' or 'expired'"),
    db: AsyncSession = Depends(get_async_session),
    current_user = Depends(current_active_user)
):
    if url_type.lower() == "expired":
        result = await db.execute(select(ExpiredURL).where(ExpiredURL.created_by == current_user.id))
        urls = result.scalars().all()
    elif url_type.lower() == "active":
        result = await db.execute(select(URL).where(URL.created_by == current_user.id))
        urls = result.scalars().all()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL type specified. Use 'active' or 'expired'."
        )

    urls.sort(key=lambda url: url.created_at, reverse=True)
    return [create_url_list_response(url) for url in urls]


@router.post("/shorten", response_model=URLResponse, summary="Create a custom shortened URL")
async def create_custom_url(
        custom_data: URLCustomCreate,
        db: AsyncSession = Depends(get_async_session),
        current_user=Depends(current_active_user)
):
    if custom_data.expiration <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiration time must be in the future."
        )

    result = await db.execute(select(URL).where(URL.short_code == custom_data.short_code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Short code already exists. Please choose another one."
        )

    new_url = URL(
        short_code=custom_data.short_code,
        original_url=custom_data.original_url,
        created_at=datetime.now(timezone.utc),
        expires_at=custom_data.expiration,
        created_by=current_user.id,
    )
    db.add(new_url)
    await db.commit()
    await db.refresh(new_url)
    return create_url_response(new_url)


@router.get("/search", summary="Search for short links by original URL", response_model=List[URLResponse])
async def search_url(
        original_url: str,
        db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(select(URL).where(URL.original_url == original_url))
    urls = result.scalars().all()
    if not urls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching URLs found.")
    return [create_url_response(url) for url in urls]


@router.get("/{short_code}", summary="Redirect to the original URL")
async def get_url(
        short_code: str,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_async_session),
        no_redirect: bool = False
):
    cached_original_url = await get_cache(short_code)
    if cached_original_url:
        background_tasks.add_task(update_url_background, short_code)
        if no_redirect:
            return {"redirect_url": cached_original_url}
        return RedirectResponse(url=cached_original_url)

    url_entry = await get_url_by_shortcode(db, short_code)
    if not url_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")
    if url_entry.expires_at and datetime.now(timezone.utc) > url_entry.expires_at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL expired")

    await store_short_code(short_code, url_entry.original_url)
    background_tasks.add_task(update_url_background, short_code)
    if no_redirect:
        return {"redirect_url": url_entry.original_url}
    return RedirectResponse(url=url_entry.original_url)


@router.delete("/{short_code}", summary="Move a short link to expired history for the current user")
async def delete_url(
        url_entry: URL = Depends(get_user_owned_url),
        db: AsyncSession = Depends(get_async_session)
):
    expired_url = ExpiredURL(
        id=url_entry.id,
        short_code=url_entry.short_code,
        original_url=url_entry.original_url,
        created_at=url_entry.created_at,
        expires_at=url_entry.expires_at,
        created_by=url_entry.created_by,
        hit_count=url_entry.hit_count,
        last_used_at=url_entry.last_used_at,
        fixed_expiration=url_entry.fixed_expiration,
        moved_at=datetime.now(timezone.utc)
    )
    db.add(expired_url)
    await db.delete(url_entry)

    await delete_cache(url_entry.short_code)

    await db.commit()
    return {"detail": "URL moved to expired history successfully"}

@router.put("/{short_code}", response_model=URLResponse, summary="Update short link for the current user")
async def update_url(
    update_data: URLUpdateRequest,
    url_entry: URL = Depends(get_user_owned_url),
    db: AsyncSession = Depends(get_async_session)
):
    new_original_url = update_data.original_url or url_entry.original_url
    old_short_code = url_entry.short_code

    if update_data.regenerate:
        new_short_code = await generate_unique_short_code(new_original_url)
        url_entry.short_code = new_short_code
        await delete_cache(old_short_code)
        await store_short_code(new_short_code, new_original_url)
    else:
        await store_short_code(old_short_code, new_original_url)

    url_entry.original_url = new_original_url

    await db.commit()
    await db.refresh(url_entry)
    return create_url_response(url_entry)


@router.get("/{short_code}/stats", summary="Get statistics for a short link")
async def get_url_stats(
        short_code: str,
        db: AsyncSession = Depends(get_async_session),
):
    url_entry = await get_url_by_shortcode(db, short_code)
    if not url_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="URL not found")

    stats = {
        "original_url": url_entry.original_url,
        "created_at": url_entry.created_at,
        "hit_count": url_entry.hit_count,
        "last_used_at": url_entry.last_used_at
    }
    return stats