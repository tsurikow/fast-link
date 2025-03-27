import pytest
from unittest.mock import AsyncMock
from backend.app.services.shortener import generate_unique_short_code

@pytest.mark.asyncio(loop_scope="session")
async def test_generate_unique_short_code(mocker):
    mocker.patch("backend.app.services.shortener.check_collision", new_callable=AsyncMock, return_value=False)
    mocker.patch("backend.app.services.shortener.store_short_code", new_callable=AsyncMock, return_value=True)

    url = "https://example.com/some/long/url"
    short_code = await generate_unique_short_code(url)
    assert isinstance(short_code, str)
    assert len(short_code) == 6