from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Port on which the Streamlit app will run
    STREAMLIT_PORT: int = Field(..., env="STREAMLIT_PORT")

    # URL for the FastAPI backend that the Streamlit app will interact with
    FASTAPI_URL: str = Field(..., env="FASTAPI_URL")
    FASTAPI_PORT: int = Field(..., env="FASTAPI_PORT")

    # Optional: A title for your Streamlit app
    APP_TITLE: str = Field(..., env="APP_TITLE")
    APP_URL: str = Field(..., env="APP_URL")

settings = Settings()
