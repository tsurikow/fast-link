import pytest
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from backend.app.models.url import URL
from backend.app.api.routes.url import get_url_stats

async def dummy_session_generator(session):
    yield session

@pytest.mark.asyncio
async def test_get_url_stats_not_found(mocker):
    mocker.patch("backend.app.api.routes.url.get_url_by_shortcode", return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await get_url_stats("nonexistent")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "URL not found"

@pytest.mark.asyncio
async def test_get_url_stats_success(mocker):
    now = datetime.now(timezone.utc)
    dummy_url = URL(
        id="11111111-1111-1111-1111-111111111111",
        short_code="test123",
        original_url="https://example.com",
        created_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=1),
        hit_count=5,
        last_used_at=now - timedelta(minutes=30)
    )
    mocker.patch("backend.app.api.routes.url.get_url_by_shortcode", return_value=dummy_url)

    stats = await get_url_stats("test123")
    assert stats["original_url"] == dummy_url.original_url
    assert stats["hit_count"] == dummy_url.hit_count
    assert stats["created_at"].isoformat() == dummy_url.created_at.isoformat()
    assert stats["last_used_at"].isoformat() == dummy_url.last_used_at.isoformat()