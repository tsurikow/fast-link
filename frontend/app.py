import requests
import streamlit as st

# Import configuration from core/config.py
from core.config import settings
from loguru import logger

# Configure Loguru to log to stdout and a log file.
logger.remove()
logger.add("stdout", format="{time} {level} {message}", level="INFO")
logger.add("app.log", format="{time} {level} {message}", level="INFO",
           rotation="10 MB",
           retention="10 days",
           compression="zip")

# Build the FastAPI URL using settings
FASTAPI_URL = f"{settings.FASTAPI_URL}:{settings.FASTAPI_PORT}"
APP_TITLE = getattr(settings, "APP_TITLE", "Fast-Link Frontend")

logger.info("Starting Streamlit app", extra={"FASTAPI_URL": FASTAPI_URL, "APP_TITLE": APP_TITLE})


def login_user(username: str, password: str) -> str:
    """Call FastAPI /auth/jwt/login endpoint to authenticate the user."""
    url = f"{FASTAPI_URL}/auth/jwt/login"
    payload = {"username": username, "password": password}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    logger.debug(f"Attempting login for user: {username} with url: {url}")

    # Send as form data (required by OAuth2PasswordRequestForm)
    response = requests.post(url, data=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        logger.info("Login successful", extra={"username": username})
        return data.get("access_token")
    else:
        logger.error(f"Login failed: {response}",
                     extra={"username": username,
                            "status_code": response.status_code})
        return None


def register_user(username: str, email: str, password: str) -> bool:
    """Call FastAPI /auth/register endpoint to register a new user."""
    url = f"{FASTAPI_URL}/auth/register"
    payload = {"username": username, "email": email, "password": password}
    logger.debug(f"Registering user: {username} at {url}")
    response = requests.post(url, json=payload)
    if response.status_code == 201:
        logger.info("User registered successfully", extra={"username": username})
        return True
    else:
        logger.error(f"User registration failed: {response}",
                     extra={"username": username, "status_code": response.status_code})
        return False


def create_short_url(original_url: str, token: str) -> str:
    """Call FastAPI /urls endpoint to create a short link."""
    url = f"{FASTAPI_URL}/urls/"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"original_url": original_url, "expires_in_minutes": 0}
    logger.debug(f"Creating short URL for: {original_url}")
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in (200, 201):
        data = response.json()
        logger.info("Short URL created", extra={"short_code": data.get("short_code")})
        return data.get("short_code")
    else:
        logger.error("Failed to create short URL", extra={"status_code": response.status_code})
        return None


def get_current_user_info(token: str) -> dict:
    """Fetch current user information from /users/me."""
    url = f"{FASTAPI_URL}/users/me"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error("Failed to fetch current user info",
                     extra={"status_code": response.status_code})
        return {}


# --- Streamlit UI ---

def main():
    st.title(APP_TITLE)

    # Initialize token in session state
    if "token" not in st.session_state:
        st.session_state.token = None

    # Navigation menu
    menu = st.sidebar.radio("Navigation",
                            ["Login",
                             "Register",
                             "Current User",
                             "Create Short Link"])

    if menu == "Login":
        st.header("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            token = login_user(username, password)
            if token:
                st.session_state.token = token
                st.success("Logged in successfully!")
            else:
                st.error("Login failed. Check your credentials.")

    elif menu == "Register":
        st.header("Register")
        username = st.text_input("Username", key="reg_username")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        if st.button("Register"):
            if register_user(username, email, password):
                st.success("Registration successful! Please log in.")
            else:
                st.error("Registration failed. Try a different username or email.")

    elif menu == "Current User":
        st.header("Current User Information")
        if st.session_state.token:
            user_info = get_current_user_info(st.session_state.token)
            if user_info:
                st.json(user_info)
            else:
                st.error("Failed to retrieve current user information.")
        else:
            st.warning("You are not logged in.")

    elif menu == "Create Short Link":
        if not st.session_state.token:
            st.error("You must be logged in to create a short link.")
        else:
            st.header("Create a New Short Link")
            original_url = st.text_input("Enter the URL to shorten")
            if st.button("Shorten URL"):
                short_code = create_short_url(original_url, st.session_state.token)
                if short_code:
                    st.success(f"Short link created: {short_code}")
                    st.write(f"Access it at: {FASTAPI_URL}/{short_code}")
                else:
                    st.error("Failed to create short link. Try again later.")


if __name__ == "__main__":
    main()
