import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from sqlalchemy.future import select
from backend.app.services.url_helpers import update_url_background
from backend.app.services.expiration import move_expired_urls
from backend.app.models.url import URL
from backend.app.core.config import settings

class DummyScalarResult:
    async def all(self):
        return []
async def dummy_session_generator(session):
    yield session

class DummyScalarResult:
    def all(self):
        return []

async def dummy_session_generator(session):
    yield session

@pytest.mark.asyncio(loop_scope="session")
async def test_update_url_background_not_found(mocker):
    dummy_session = AsyncMock()
    dummy_result = AsyncMock()
    dummy_result.scalar_one_or_none = AsyncMock(return_value=None)
    dummy_result.scalars = lambda: DummyScalarResult()
    dummy_session.execute.return_value = dummy_result

    mocker.patch(
        "backend.app.services.url_helpers.get_async_session",
        return_value=dummy_session_generator(dummy_session)
    )

    moved_codes = await move_expired_urls(dummy_session)
    assert moved_codes == []
    dummy_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_update_url_background_fixed_expiration(mocker):
    dummy_session = AsyncMock()
    dummy_url = URL(
        id="11111111-1111-1111-1111-111111111111",
        short_code="fixexp",
        original_url="https://fixed.com",
        created_at=datetime.now(timezone.utc) - timedelta(hours=1),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        hit_count=0,
        created_by=None,
        last_used_at=datetime.now(timezone.utc),
        fixed_expiration=True,
    )
    dummy_result = AsyncMock()
    dummy_result.scalar_one_or_none = lambda: dummy_url
    dummy_session.execute.return_value = dummy_result

    mocker.patch(
        "backend.app.services.url_helpers.get_async_session",
        return_value=dummy_session_generator(dummy_session)
    )

    await update_url_background("fixexp")
    assert dummy_session.execute.call_count >= 2
    dummy_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_update_url_background_non_fixed_expiration(mocker):
    dummy_session = AsyncMock()
    dummy_url = URL(
        id="22222222-2222-2222-2222-222222222222",
        short_code="nonfix",
        original_url="https://nonfixed.com",
        created_at=datetime.now(timezone.utc) - timedelta(hours=1),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        hit_count=3,
        created_by=None,
        last_used_at=datetime.now(timezone.utc),
        fixed_expiration=False,
    )
    dummy_result = AsyncMock()
    dummy_result.scalar_one_or_none = lambda: dummy_url
    dummy_session.execute.return_value = dummy_result

    mocker.patch(
        "backend.app.services.url_helpers.get_async_session",
        return_value=dummy_session_generator(dummy_session)
    )

    await update_url_background("nonfix")
    assert dummy_session.execute.call_count >= 2
    dummy_session.commit.assert_called_once()