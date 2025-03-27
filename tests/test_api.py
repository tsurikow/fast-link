import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.models.url import URL

async def register_and_login(ac: AsyncClient, email: str, password: str):
    reg_response = await ac.post("/auth/register", json={
        "username": email.split("@")[0],
        "email": email,
        "password": password
    })

    login_data = {"username": email, "password": password}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    login_response = await ac.post("/auth/jwt/login", data=login_data, headers=headers)
    assert login_response.status_code == 200, login_response.text
    token = login_response.json().get("access_token")
    return token

transport = ASGITransport(app=app)


@pytest.mark.asyncio(loop_scope="session")
async def test_root_endpoint():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

@pytest.mark.asyncio(loop_scope="session")
async def test_register_and_login():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "testuser@example.com", "testpassword")
        assert token is not None

@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_redirect_url_unauthenticated():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_response = await ac.post("/url", json={
            "original_url": "https://example.com"
        })
        assert create_response.status_code == 200, create_response.text
        data = create_response.json()
        short_code = data["short_code"]

        redirect_response = await ac.get(f"/{short_code}?no_redirect=true")
        assert redirect_response.status_code == 200, redirect_response.text
        assert "redirect_url" in redirect_response.json()


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_redirect_url_authenticated():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "authuser@example.com", "secret123")
        headers = {"Authorization": f"Bearer {token}"}

        create_response = await ac.post("/url", json={
            "original_url": "https://authenticated.com"
        }, headers=headers)
        assert create_response.status_code == 200, create_response.text
        data = create_response.json()
        short_code = data["short_code"]

        redirect_response = await ac.get(f"/{short_code}?no_redirect=true", headers=headers)
        assert redirect_response.status_code == 200, redirect_response.text
        assert "redirect_url" in redirect_response.json()


@pytest.mark.asyncio(loop_scope="session")
async def test_get_my_urls():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "myurls@example.com", "mypassword")
        headers = {"Authorization": f"Bearer {token}"}

        for url in ["https://example.com/one", "https://example.com/two"]:
            response = await ac.post("/url", json={"original_url": url}, headers=headers)
            assert response.status_code == 200, response.text

        my_urls_response = await ac.get("/my_urls?url_type=active", headers=headers)
        assert my_urls_response.status_code == 200, my_urls_response.text
        data = my_urls_response.json()
        assert isinstance(data, list)
        assert len(data) >= 2


@pytest.mark.asyncio(loop_scope="session")
async def test_create_custom_url():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "customuser@example.com", "custompass")
        headers = {"Authorization": f"Bearer {token}"}

        future_expiration = (await ac.get("/url")).json().get(
            "created_at")
        custom_payload = {
            "original_url": "https://custom.com",
            "short_code": "cust01",
            "expiration": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        }
        custom_response = await ac.post("/shorten", json=custom_payload, headers=headers)
        assert custom_response.status_code == 200, custom_response.text
        data = custom_response.json()
        assert data["short_code"] == "cust01"


@pytest.mark.asyncio(loop_scope="session")
async def test_create_url_existing_authenticated():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "existing@example.com", "password123")
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"original_url": f"https://example.com/?ts={int(datetime.now().timestamp() * 1000)}"}

        response1 = await ac.post("/url", json=payload, headers=headers)
        assert response1.status_code == 200, response1.text
        data1 = response1.json()
        short_code1 = data1.get("short_code")
        assert short_code1 is not None

        response2 = await ac.post("/url", json=payload, headers=headers)
        assert response2.status_code == 200, response2.text
        data2 = response2.json()
        short_code2 = data2.get("short_code")

        assert short_code1 == short_code2, "Expected the same short code when URL already exists."


@pytest.mark.asyncio(loop_scope="session")
async def test_get_my_urls_and_invalid_url_type():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "myurlsuser@example.com", "mypassword")
        headers = {"Authorization": f"Bearer {token}"}

        for url in ["https://site.com/one", "https://site.com/two"]:
            res = await ac.post("/url", json={"original_url": url}, headers=headers)
            assert res.status_code == 200, res.text

        res_active = await ac.get("/my_urls", params={"url_type": "active"}, headers=headers)
        assert res_active.status_code == 200, res_active.text
        active_list = res_active.json()
        assert isinstance(active_list, list)
        assert len(active_list) >= 2

        res_expired = await ac.get("/my_urls", params={"url_type": "expired"}, headers=headers)
        assert res_expired.status_code == 200, res_expired.text

        res_invalid = await ac.get("/my_urls", params={"url_type": "invalid"}, headers=headers)
        assert res_invalid.status_code == 400, res_invalid.text

@pytest.mark.asyncio(loop_scope="session")
async def test_create_custom_url_errors():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "customuser@example.com", "custompass")
        headers = {"Authorization": f"Bearer {token}"}

        past_exp = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        payload = {
            "original_url": "https://custom.com",
            "short_code": "custom",
            "expiration": past_exp
        }
        res_past = await ac.post("/shorten", json=payload, headers=headers)
        assert res_past.status_code == 400, res_past.text

        future_exp = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        payload["expiration"] = future_exp
        res_valid = await ac.post("/shorten", json=payload, headers=headers)
        assert res_valid.status_code == 200, res_valid.text

        res_duplicate = await ac.post("/shorten", json=payload, headers=headers)
        assert res_duplicate.status_code == 400, res_duplicate.text

@pytest.mark.asyncio(loop_scope="session")
async def test_search_url():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_create = await ac.post("/url", json={"original_url": "https://search.com"})
        assert res_create.status_code == 200, res_create.text

        res_search = await ac.get("/search", params={"original_url": "https://search.com"})
        assert res_search.status_code == 200, res_search.text
        results = res_search.json()
        assert isinstance(results, list)
        assert len(results) >= 1

        res_search_none = await ac.get("/search", params={"original_url": "https://nonexistent.com"})
        assert res_search_none.status_code == 404, res_search_none.text

@pytest.mark.asyncio(loop_scope="session")
async def test_get_url_stats():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_create = await ac.post("/url", json={"original_url": "https://stats.com"})
        assert res_create.status_code == 200, res_create.text
        short_code = res_create.json()["short_code"]

        res_stats = await ac.get(f"/{short_code}/stats")
        assert res_stats.status_code == 200, res_stats.text
        stats = res_stats.json()
        assert "original_url" in stats
        assert "hit_count" in stats

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_url():

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "deleteuser@example.com", "deletepass")
        headers = {"Authorization": f"Bearer {token}"}
        res_create = await ac.post("/url", json={"original_url": "https://delete.com"}, headers=headers)
        assert res_create.status_code == 200, res_create.text
        short_code = res_create.json()["short_code"]

        res_delete = await ac.delete(f"/{short_code}", headers=headers)
        assert res_delete.status_code == 200, res_delete.text
        assert "URL moved to expired history" in res_delete.json()["detail"]

@pytest.mark.asyncio(loop_scope="session")
async def test_update_url():

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "updateuser@example.com", "updatepass")
        headers = {"Authorization": f"Bearer {token}"}
        res_create = await ac.post("/url", json={"original_url": "https://update.com"}, headers=headers)
        assert res_create.status_code == 200, res_create.text
        original_data = res_create.json()
        original_code = original_data["short_code"]

        update_payload = {"original_url": "https://update-new.com", "regenerate": False}
        res_update = await ac.put(f"/{original_code}", json=update_payload, headers=headers)
        assert res_update.status_code == 200, res_update.text
        updated_data = res_update.json()
        assert updated_data["short_code"] == original_code
        assert updated_data["original_url"] == "https://update-new.com"

        update_payload_regen = {"original_url": "https://update-new.com", "regenerate": True}
        res_update_regen = await ac.put(f"/{original_code}", json=update_payload_regen, headers=headers)
        assert res_update_regen.status_code == 200, res_update_regen.text
        updated_data_regen = res_update_regen.json()
        assert updated_data_regen["short_code"] != original_code

@pytest.mark.asyncio(loop_scope="session")
async def test_create_url_missing_field():

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/url", json={})
    assert response.status_code == 422

@pytest.mark.asyncio(loop_scope="session")
async def test_redirect_nonexistent_short_code():

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/nonexistent?no_redirect=true")
    assert response.status_code == 404


@pytest.mark.asyncio(loop_scope="session")
async def test_update_url_invalid_payload():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "update_invalid@example.com", "password123")
        headers = {"Authorization": f"Bearer {token}"}

        create_response = await ac.post("/url", json={"original_url": "https://update-invalid.com"}, headers=headers)
        assert create_response.status_code == 200, create_response.text
        short_code = create_response.json()["short_code"]

        update_response = await ac.put(f"/{short_code}", json={"original_url": 12345, "regenerate": True},
                                       headers=headers)
        assert update_response.status_code == 422, update_response.text

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_url_not_owned():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token_a = await register_and_login(ac, "usera@example.com", "passwordA")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        create_response = await ac.post("/url", json={"original_url": "https://notowned.com"}, headers=headers_a)
        assert create_response.status_code == 200, create_response.text
        short_code = create_response.json()["short_code"]

        token_b = await register_and_login(ac, "userb@example.com", "passwordB")
        headers_b = {"Authorization": f"Bearer {token_b}"}

        delete_response = await ac.delete(f"/{short_code}", headers=headers_b)
        assert delete_response.status_code == 403, delete_response.text

@pytest.mark.asyncio(loop_scope="session")
async def test_custom_short_code_duplicate():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "customuser@example.com", "custompass")
        headers = {"Authorization": f"Bearer {token}"}

        unique_code = "cust01" + str(int(datetime.now(timezone.utc).timestamp()))
        custom_payload = {
            "original_url": "https://custom.com",
            "short_code": unique_code,
            "expiration": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        }
        response1 = await ac.post("/shorten", json=custom_payload, headers=headers)
        assert response1.status_code == 200, response1.text

        response2 = await ac.post("/shorten", json=custom_payload, headers=headers)
        assert response2.status_code in (400, 409), response2.text
        detail = response2.json().get("detail", "")
        assert "already exists" in detail.lower(), f"Unexpected error detail: {detail}"

@pytest.mark.asyncio(loop_scope="session")
async def test_search_url_invalid_params():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/search")
    assert response.status_code == 422, response.text

@pytest.mark.asyncio(loop_scope="session")
async def test_get_stats_nonexistent():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/nonexistent/stats")
    assert response.status_code == 404, response.text


@pytest.mark.asyncio(loop_scope="session")
async def test_update_url_without_regenerate():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "updateuser@example.com", "updatepass")
        headers = {"Authorization": f"Bearer {token}"}

        create_response = await ac.post("/url", json={"original_url": "https://update-no-regenerate.com"},
                                        headers=headers)
        assert create_response.status_code == 200, create_response.text
        data = create_response.json()
        original_code = data["short_code"]

        update_payload = {"original_url": "https://update-no-regenerate-new.com", "regenerate": False}
        update_response = await ac.put(f"/{original_code}", json=update_payload, headers=headers)
        assert update_response.status_code == 200, update_response.text
        updated_data = update_response.json()
        assert updated_data["short_code"] == original_code
        assert updated_data["original_url"] == "https://update-no-regenerate-new.com"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_url_with_regenerate(mocker):
    from sqlalchemy.ext.asyncio.session import AsyncSession
    mocker.patch.object(AsyncSession, "refresh", new_callable=AsyncClient)
    from unittest.mock import AsyncMock
    mocker.patch("sqlalchemy.ext.asyncio.session.AsyncSession.refresh", new=AsyncMock())

    from backend.app.api.routes.url import get_user_owned_url
    async def fake_get_user_owned_url(short_code: str, db=None, current_user=None):
        return URL(
            id="dummy-id",
            short_code="oldcode",
            original_url="https://old.com",
            created_at=datetime.now(timezone.utc) - timedelta(hours=1),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_by="user123",
            hit_count=10,
            last_used_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            fixed_expiration=False
        )

    app.dependency_overrides[get_user_owned_url] = fake_get_user_owned_url

    mocker.patch(
        "backend.app.api.routes.url.generate_unique_short_code",
        return_value="newcode"
    )

    delete_cache_called = False
    store_cache_called = False

    async def fake_delete_cache(code: str):
        nonlocal delete_cache_called
        delete_cache_called = True

    async def fake_store_short_code(code: str, original_url: str):
        nonlocal store_cache_called
        store_cache_called = True

    mocker.patch("backend.app.api.routes.url.delete_cache", side_effect=fake_delete_cache)
    mocker.patch("backend.app.api.routes.url.store_short_code", side_effect=fake_store_short_code)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token = await register_and_login(ac, "updateuser@example.com", "updatepass")
        headers = {"Authorization": f"Bearer {token}"}
        update_payload = {"original_url": "https://new.com", "regenerate": True}
        response = await ac.put("/oldcode", json=update_payload, headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["short_code"] == "newcode", f"Expected 'newcode', got {data['short_code']}"
        assert data["original_url"] == "https://new.com"

    assert delete_cache_called, "delete_cache was not called"
    assert store_cache_called, "store_short_code was not called"