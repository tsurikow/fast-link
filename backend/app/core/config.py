from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # Redis configuration
    REDIS_HOST: str = Field("redis", env="REDIS_HOST")  # default to service name 'redis'
    REDIS_PORT: int = Field(..., env="REDIS_PORT")
    REDIS_PASSWORD: str = Field(..., env="REDIS_PASSWORD")
    REDIS_DATA: str = Field(..., env="REDIS_DATA")

    # Postgres configuration
    POSTGRES_HOST: str = Field("postgres", env="POSTGRES_HOST")  # default to service name 'postgres'
    POSTGRES_PORT: int = Field(..., env="POSTGRES_PORT")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_DATA: str = Field(..., env="POSTGRES_DATA")

    # Application ports
    FASTAPI_PORT: int = Field(..., env="FASTAPI_PORT")
    STREAMLIT_PORT: int = Field(..., env="STREAMLIT_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()