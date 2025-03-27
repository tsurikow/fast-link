import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio(loop_scope="session")
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

@pytest.mark.asyncio(loop_scope="session")
async def test_register_and_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register a new user
        reg_response = await ac.post("/auth/register", json={
            "email": "testuser@example.com",
            "password": "testpassword"
        })
        # Expect 201 Created for registration
        assert reg_response.status_code == 201, reg_response.text

        # Login using form data; note that we use the email as the username here
        login_data = {"username": "testuser@example.com", "password": "testpassword"}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        login_response = await ac.post("/auth/jwt/login", data=login_data, headers=headers)
        assert login_response.status_code == 200, login_response.text
        token = login_response.json().get("access_token")
        assert token is not None

@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_redirect_url_unauthenticated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create a new short URL without authentication
        create_response = await ac.post("/url", json={
            "original_url": "https://example.com"
        })
        assert create_response.status_code == 200, create_response.text
        data = create_response.json()
        short_code = data["short_code"]

        # Test the redirect endpoint with no_redirect flag for testing purposes
        redirect_response = await ac.get(f"/{short_code}?no_redirect=true")
        assert redirect_response.status_code == 200, redirect_response.text
        assert "redirect_url" in redirect_response.json()