from datetime import datetime, timezone

from sqlalchemy.future import select

from backend.app.models.url import URL, ExpiredURL


async def move_expired_urls(session) -> list[str]:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(URL).where(
            URL.expires_at != None,
            URL.expires_at < now
        )
    )
    expired_urls = result.scalars().all()
    moved_codes = []
    for url in expired_urls:
        # Create an ExpiredURL record copying fields from url except created_by.
        expired = ExpiredURL(
            id=url.id,
            short_code=url.short_code,
            original_url=url.original_url,
            created_at=url.created_at,
            expires_at=url.expires_at,
            moved_at=datetime.now(timezone.utc)
        )
        # Transfer associated users (many-to-many relationship).
        expired.users = url.users[:]  # shallow copy the list of associated users

        session.add(expired)
        await session.delete(url)
        moved_codes.append(url.short_code)
    await session.commit()
    return moved_codes