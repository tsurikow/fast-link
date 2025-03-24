from datetime import datetime, timezone
from sqlalchemy.future import select
from backend.app.models.url import URL, ExpiredURL

async def move_expired_urls(session) -> list[str]:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(URL).where(URL.expires_at != None, URL.expires_at < now)
    )
    expired_urls = result.scalars().all()
    moved_codes = []
    for url in expired_urls:
        expired = ExpiredURL(
            id=url.id,
            short_code=url.short_code,
            original_url=url.original_url,
            created_at=url.created_at,
            expires_at=url.expires_at,
            hit_count=url.hit_count,
            moved_at=now,
            created_by=url.created_by,
            last_used_at=url.last_used_at,
            fixed_expiration=url.fixed_expiration,
        )
        session.add(expired)
        await session.delete(url)
        moved_codes.append(url.short_code)
    await session.commit()
    return moved_codes