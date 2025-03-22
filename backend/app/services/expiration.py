from datetime import datetime, timezone

from sqlalchemy.future import select

from backend.app.models.url import URL, ExpiredURL


async def move_expired_urls(session):
    now = datetime.now(timezone.utc)
    # Query all URLs where expires_at is not null and is less than current time
    result = await session.execute(select(URL).where(
        URL.expires_at is not None,
        URL.expires_at < now))
    expired_urls = result.scalars().all()

    for url in expired_urls:
        # Create a new ExpiredURL record with details from URL
        expired = ExpiredURL(
            id=url.id,  # optionally re-use the same id, or generate a new one
            short_code=url.short_code,
            original_url=url.original_url,
            created_at=url.created_at,
            expires_at=url.expires_at,
            created_by=url.created_by,
            moved_at=datetime.now(timezone.utc)
        )
        session.add(expired)
        # Delete the URL from the main table
        await session.delete(url)
    await session.commit()
