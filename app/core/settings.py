"""
Application Configuration.
"""

import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "TradeBrain"
    API_VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    WORKERS: int = int(os.getenv("WORKERS", 1))

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./tradebrain.db")
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 24 * 60))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    # Scanner scheduling settings
    SCANNER_ENABLED: bool = os.getenv("SCANNER_ENABLED", "true").lower() == "true"
    SCANNER_CRON_EXPRESSION: str = os.getenv("SCANNER_CRON_EXPRESSION", "0 9,15 * * 1-5")  # 9 AM & 3 PM on weekdays
    SCANNER_MIN_CONFIDENCE: int = int(os.getenv("SCANNER_MIN_CONFIDENCE", 75))


settings = Settings()
