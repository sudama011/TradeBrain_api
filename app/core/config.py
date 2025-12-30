import os

from dotenv import load_dotenv

# Load variables from .env file immediately
load_dotenv()


class Settings:
    APP_NAME: str = "TradeBrain"
    API_VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # Options: development, production
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    TAVILY_API_KEY: str | None = os.getenv("TAVILY_API_KEY")
    API_KEY: str | None = os.getenv("API_KEY")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./tradebrain.db")
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = int(os.getenv("WORKERS", 1))


settings = Settings()
