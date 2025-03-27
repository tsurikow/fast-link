import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # model_config = SettingsConfigDict(
    #     env_file=os.getenv("ENV_FILE", ".env"),
    #     env_file_encoding="utf-8",
    #     extra="ignore"  # Allow extra env variables without raising errors.
    # )

    # Redis configuration
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_DATA: str

    # Postgres configuration
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_DATA: str

    # FastAPI configuration
    FASTAPI_PORT: int

    # Security configuration for JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # URL shortener configuration
    URL_EXPIRE_MINUTES: int
    APP_URL: str
    EXPIRATION_CHECK_INTERVAL: int


settings = Settings()
