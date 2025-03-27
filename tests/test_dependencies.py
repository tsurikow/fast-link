import pytest
from fastapi import HTTPException
from backend.app.services.url_dependencies import get_user_owned_url
from backend.app.models.url import URL
from datetime import datetime, timedelta, timezone

class DummyResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

class DummySession:
    # We'll set self.value externally.
    async def execute(self, statement):
        return DummyResult(self.value)

@pytest.fixture
def dummy_current_user():
    return type("DummyUser", (), {"id": "dummy_user_id"})

@pytest.fixture
def dummy_url(dummy_current_user):
    return URL(
        id="11111111-1111-1111-1111-111111111111",
        short_code="abc123",
        original_url="https://example.com",
        created_at=datetime.now(timezone.utc) - timedelta(hours=1),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        created_by=dummy_current_user.id,
    )

@pytest.mark.asyncio
async def test_get_user_owned_url_success(dummy_url, dummy_current_user):
    dummy_session = DummySession()
    dummy_session.value = dummy_url

    result = await get_user_owned_url("abc123", db=dummy_session, current_user=dummy_current_user)
    assert result == dummy_url

@pytest.mark.asyncio
async def test_get_user_owned_url_not_found(dummy_current_user):
    dummy_session = DummySession()
    dummy_session.value = None

    with pytest.raises(HTTPException) as excinfo:
        await get_user_owned_url("nonexistent", db=dummy_session, current_user=dummy_current_user)
    assert excinfo.value.status_code == 404

@pytest.mark.asyncio
async def test_get_user_owned_url_forbidden(dummy_url):
    dummy_session = DummySession()
    dummy_session.value = dummy_url

    different_user = type("DummyUser", (), {"id": "other_user_id"})

    with pytest.raises(HTTPException) as excinfo:
        await get_user_owned_url("abc123", db=dummy_session, current_user=different_user)
    assert excinfo.value.status_code == 403