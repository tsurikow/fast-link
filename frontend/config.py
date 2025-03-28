from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Port on which the Streamlit app will run
    STREAMLIT_PORT: int

    # URL for the FastAPI backend that the Streamlit app will interact with
    FASTAPI_URL: str
    FASTAPI_PORT: int

    # Optional: A title for your Streamlit app
    APP_TITLE: str
    APP_URL: str

settings = Settings()
