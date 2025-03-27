from locust import HttpUser, task, between

class FastLinkUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def create_url(self):
        self.client.post("/urls", json={
            "original_url": "https://example.com",
            "expires_in_minutes": 1
        })

    @task
    def get_redirect(self):
        self.client.get("/urls/testcode?no_redirect=true")