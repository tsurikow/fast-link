from datetime import datetime, timedelta, timezone
from sqlalchemy import update
from sqlalchemy.future import select
from backend.app.core.config import settings
from backend.app.db.session import get_async_session
from backend.app.models.url import URL
from backend.app.core.logging_config import logger


async def update_url_background(short_code: str) -> None:
    session_gen = get_async_session()
    session = await session_gen.__anext__()
    try:
        result = await session.execute(select(URL).where(URL.short_code == short_code))
        url_entry = result.scalar_one_or_none()
        if not url_entry:
            return

        if url_entry.fixed_expiration:
            stmt = (
                update(URL)
                .where(URL.short_code == short_code)
                .values(
                    hit_count=URL.hit_count + 1
                )
            )
        else:
            new_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.URL_EXPIRE_MINUTES)
            stmt = (
                update(URL)
                .where(URL.short_code == short_code)
                .values(
                    expires_at=new_expires_at,
                    hit_count=URL.hit_count + 1
                )
            )
        logger.debug(f"Updating URL {short_code} in background")
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Successfully updated URL {short_code}")
    except Exception as e:
        logger.error(f"Error updating URL {short_code}: {e}")
        raise
    finally:
        await session.close()