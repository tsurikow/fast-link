import pytest
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.future import select

from backend.app.models.url import URL, ExpiredURL
from backend.app.api.routes.url import get_my_urls
from backend.app.api.schemas.url import URLListResponse

class DummyScalarResult:
    def __init__(self, values):
        self._values = values
    def all(self):
        return self._values

class DummyResult:
    def __init__(self, values):
        self._values = values
    def scalars(self):
        return DummyScalarResult(self._values)

class DummySession:
    async def execute(self, query):
        return DummyResult(self.result)

@pytest.fixture
def dummy_user():
    return type("DummyUser", (), {"id": "user123"})

async def dummy_session_generator(session: DummySession):
    yield session


@pytest.mark.asyncio
async def test_get_my_urls_active(dummy_user):
    now = datetime.now(timezone.utc)
    active_url = URL(
        id="url1",
        short_code="active1",
        original_url="https://active.com",
        created_at=now - timedelta(minutes=5),
        expires_at=now + timedelta(hours=1),
        created_by=dummy_user.id,
        hit_count=0,
        fixed_expiration=False
    )

    dummy_session = DummySession()
    dummy_session.result = [active_url]

    result = await get_my_urls(
        url_type="active",
        db=dummy_session,
        current_user=dummy_user
    )

    assert isinstance(result, list)
    assert len(result) == 1
    response_item = result[0]
    assert response_item.model_dump()["original_url"]  == active_url.original_url
@pytest.mark.asyncio
async def test_get_my_urls_expired(dummy_user):
    now = datetime.now(timezone.utc)
    expired_url = ExpiredURL(
        id="url2",
        short_code="expired1",
        original_url="https://expired.com",
        created_at=now - timedelta(hours=2),
        expires_at=now - timedelta(minutes=30),
        created_by=dummy_user.id,
        hit_count=0,
        fixed_expiration=False
    )
    dummy_session = DummySession()
    dummy_session.result = [expired_url]

    result = await get_my_urls(
        url_type="expired",
        db=dummy_session,
        current_user=dummy_user
    )
    assert isinstance(result, list)
    assert len(result) == 1
    response_item = result[0]
    assert response_item.model_dump()["original_url"]  == expired_url.original_url

@pytest.mark.asyncio
async def test_get_my_urls_invalid_type(dummy_user):
    dummy_session = DummySession()
    dummy_session.result = []
    with pytest.raises(HTTPException) as excinfo:
        await get_my_urls(
            url_type="invalid",
            db=dummy_session,
            current_user=dummy_user
        )
    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid URL type specified" in excinfo.value.detail