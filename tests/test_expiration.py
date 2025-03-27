import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from backend.app.models.url import URL, ExpiredURL
from backend.app.services.expiration import move_expired_urls
from tests.conftest import TestingSessionLocal

@pytest.mark.asyncio(loop_scope="session")
async def test_move_expired_urls(db_session):
    past = datetime.now(timezone.utc) - timedelta(minutes=10)
    url = URL(
        id="11111111-1111-1111-1111-111111111111",
        short_code="expsd",
        original_url="https://expired.com",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=20),
        expires_at=past,
        hit_count=5,
        created_by=None,
        last_used_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        fixed_expiration=False,
    )
    db_session.add(url)
    await db_session.commit()

    async with TestingSessionLocal() as verify_session:
        result = await verify_session.execute(select(URL).where(URL.short_code == "expsd"))
        active_url = result.scalar_one_or_none()
        assert active_url is not None, "URL should exist before expiration move."

    async with TestingSessionLocal() as expiration_session:
        moved_codes = await move_expired_urls(expiration_session)
        assert "expsd" in moved_codes, "Expected 'expsd' to be moved to expired."

    async with TestingSessionLocal() as new_session:
        result = await new_session.execute(select(URL).where(URL.short_code == "expsd"))
        active_url = result.scalar_one_or_none()
        assert active_url is None, "URL should have been removed from active table."

        result = await new_session.execute(select(ExpiredURL).where(ExpiredURL.short_code == "expsd"))
        expired_url = result.scalar_one_or_none()
        assert expired_url is not None, "URL should be present in expired table."
        assert expired_url.original_url == "https://expired.com"
        now = datetime.now(timezone.utc)
        assert (now - expired_url.moved_at) < timedelta(seconds=5), "Moved_at timestamp is not recent."