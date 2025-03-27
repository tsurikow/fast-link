import asyncio
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from backend.app.main import app, lifespan
from backend.app.models.url import URL
from backend.app.api.routes.auth_users import fastapi_users, auth_backend
from backend.app.core.config import settings


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
        now = datetime.now(timezone.utc)
        dummy_url = URL(
            id="dummy-id",
            short_code="abc123",
            original_url="https://dummy.com",
            created_at=now - timedelta(hours=1),
            expires_at=now + timedelta(hours=1),
        )
        return DummyResult([dummy_url])

    async def close(self):
        pass

async def dummy_session_generator():
    yield DummySession()

@pytest.mark.asyncio(loop_scope="session")
async def test_lifespan_warmup(monkeypatch):
    monkeypatch.setattr("backend.app.main.get_async_session", lambda: dummy_session_generator())

    called = []

    async def fake_store_short_code(short_code, original_url):
        called.append((short_code, original_url))

    monkeypatch.setattr("backend.app.main.store_short_code", fake_store_short_code)

    async with lifespan(app):
        await asyncio.sleep(0.1)
        assert ("abc123", "https://dummy.com") in called, "Expected store_short_code to be called for the active URL."
