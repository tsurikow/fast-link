import streamlit as st
from typing import Optional, Tuple
import requests

from logging_config import logger
from config import settings

FASTAPI_URL = f"{settings.FASTAPI_URL}:{settings.FASTAPI_PORT}"


def fetch_url_list(token: Optional[str] = None) -> Tuple[list, list]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    active_url_endpoint = f"{FASTAPI_URL}/my_urls?url_type=active"
    expired_url_endpoint = f"{FASTAPI_URL}/my_urls?url_type=expired"
    try:
        active_response = requests.get(active_url_endpoint, headers=headers)
        if active_response.status_code == 200:
            active_urls = active_response.json()
        else:
            st.error(f"Failed to fetch active URLs: {active_response.status_code}")
            active_urls = []
    except Exception as e:
        st.error(f"Error fetching active URLs: {e}")
        active_urls = []

    try:
        expired_response = requests.get(expired_url_endpoint, headers=headers)
        if expired_response.status_code == 200:
            expired_urls = expired_response.json()
        else:
            st.error(f"Failed to fetch expired URLs: {expired_response.status_code}")
            expired_urls = []
    except Exception as e:
        st.error(f"Error fetching expired URLs: {e}")
        expired_urls = []

    return active_urls, expired_urls


def get_url_stats(short_code: str, token: Optional[str] = None) -> dict:
    url = f"{FASTAPI_URL}/{short_code}/stats"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to retrieve stats for {short_code}: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"Error fetching stats for {short_code}: {e}")
        return {}


def login_user(email: str, password: str) -> Optional[str]:
    url = f"{FASTAPI_URL}/auth/jwt/login"
    payload = {"username": email, "password": password}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    logger.debug(f"Attempting login for email: {email} with url: {url}")
    try:
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            logger.info("Login successful", extra={"email": email})
            return data.get("access_token")
        else:
            st.error(f"Login failed: {response.status_code}")
            logger.error("Login failed", extra={"email": email, "status_code": response.status_code})
            return None
    except Exception as e:
        st.error(f"Error during login: {e}")
        logger.error(f"Error during login: {e}")
        return None


def register_user(email: str, password: str) -> bool:
    url = f"{FASTAPI_URL}/auth/register"
    payload = {"email": email, "password": password}
    logger.debug(f"Registering user with email: {email} at {url}")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201:
            logger.info("User registered successfully", extra={"email": email})
            return True
        else:
            st.error(f"User registration failed: {response.status_code}")
            logger.error("User registration failed", extra={"email": email, "status_code": response.status_code})
            return False
    except Exception as e:
        st.error(f"Error during registration: {e}")
        logger.error(f"Error during registration: {e}")
        return False


def create_short_url(original_url: str, token: Optional[str] = None) -> Optional[str]:
    url = f"{FASTAPI_URL}/url"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    payload = {"original_url": original_url, "expires_in_minutes": 0}
    logger.debug(f"Creating short URL for: {original_url}")
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in (200, 201):
            data = response.json()
            logger.info("Short URL created", extra={"short_code": data.get("short_code")})
            return data.get("short_code")
        else:
            st.error(f"Failed to create short URL: {response.status_code}")
            logger.error("Failed to create short URL", extra={"status_code": response.status_code})
            return None
    except Exception as e:
        st.error(f"Error creating short URL: {e}")
        logger.error(f"Error creating short URL: {e}")
        return None


def create_custom_short_url(data: dict, token: str) -> Optional[str]:
    url = f"{FASTAPI_URL}/shorten"
    headers = {"Authorization": f"Bearer {token}"}
    logger.debug(f"Creating custom short URL with data: {data}")
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code in (200, 201):
            res_data = response.json()
            logger.info("Custom short URL created", extra={"short_code": res_data.get("short_code")})
            return res_data.get("short_code")
        else:
            st.error(f"Failed to create custom short URL: {response.status_code}")
            logger.error("Failed to create custom short URL", extra={"status_code": response.status_code})
            return None
    except Exception as e:
        st.error(f"Error creating custom short URL: {e}")
        logger.error(f"Error creating custom short URL: {e}")
        return None


def search_url(original_url: str) -> list:
    url = f"{FASTAPI_URL}/search"
    params = {"original_url": original_url}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"No matching URLs found: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error searching URLs: {e}")
        return []


def update_url(short_code: str, update_data: dict, token: str) -> dict:
    url = f"{FASTAPI_URL}/{short_code}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.put(url, json=update_data, headers=headers)
        if response.status_code in (200, 201):
            return response.json()
        else:
            st.error(f"Failed to update URL: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"Error updating URL: {e}")
        return {}


def delete_url(short_code: str, token: str) -> dict:
    url = f"{FASTAPI_URL}/{short_code}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to delete URL: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"Error deleting URL: {e}")
        return {}


def get_current_user_info(token: str) -> dict:
    url = f"{FASTAPI_URL}/users/me"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch current user info: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"Error fetching current user info: {e}")
        return {}