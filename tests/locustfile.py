import random
import string
from locust import HttpUser, task, between


class FastAPIUser(HttpUser):
    wait_time = between(1, 2)

    def random_string(self, length=8):
        return ''.join(random.choices(string.ascii_lowercase, k=length))

    @task
    def register_auth_create_use(self):
        random_email = f"{self.random_string()}@example.com"
        password = "secret"
        register_payload = {
            "email": random_email,
            "password": password
        }

        with self.client.post("/auth/register", json=register_payload, catch_response=True) as reg_response:
            if reg_response.status_code != 201:
                reg_response.failure(f"Registration failed: {reg_response.status_code} {reg_response.text}")
                return
            else:
                reg_response.success()

        login_payload = {
            "username": random_email,
            "password": password
        }

        with self.client.post("/auth/jwt/login", data=login_payload, catch_response=True) as login_response:
            if login_response.status_code != 200:
                login_response.failure(f"Login failed: {login_response.status_code} {login_response.text}")
                return

            token = login_response.json().get("access_token")
            if not token:
                login_response.failure("No access token found in login response")
                return
            else:
                login_response.success()

        headers = {"Authorization": f"Bearer {token}"}

        original_url = self.random_url()
        url_payload = {"original_url": original_url}

        with self.client.post("/url", json=url_payload, headers=headers, catch_response=True) as create_response:
            if create_response.status_code not in [200, 201]:
                create_response.failure(f"Failed to create short URL: {create_response.status_code}")
                return
            try:
                data = create_response.json()
                short_code = data.get("short_code")
                if not short_code:
                    create_response.failure("No short_code found in response")
                    return
            except Exception as e:
                create_response.failure(f"Error parsing JSON: {str(e)}")
                return
            create_response.success()

        get_url = f"/{short_code}?no_redirect=true"
        with self.client.get(get_url, name="/<shortcode>?no_redirect=true", headers=headers, catch_response=True) as get_response:
            if get_response.status_code == 200:
                get_response.success()
            else:
                get_response.failure(f"Failed to get URL with short code {short_code}")

    def random_url(self):
        return "https://example.com/" + ''.join(random.choices(string.ascii_lowercase, k=5))