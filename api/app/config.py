"""Configuration loaded from environment variables.

Why this file exists:
- Centralizes all env var access into one typed object.
- Pydantic validates types at startup. If DB_PORT is missing or non-numeric,
  the app fails immediately and loudly instead of crashing on the first DB query.
- Anywhere in the app that needs config does `from app.config import settings`.
  No more os.getenv() scattered through the codebase.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# .env lives at the project root, two directories up from this file:
# api/app/config.py -> api/app -> api -> stock-analysis (root with .env)
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    db_host: str
    db_port: int
    db_name: str
    db_name_test: str = "trading_test"
    db_user: str
    db_password: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,  # DB_HOST and db_host both work
    )

    @property
    def database_url(self) -> str:
        """Build the asyncpg connection string from individual parts."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    @property
    def database_url_test(self) -> str:
        """Build the asyncpg connection string for the test DB."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name_test}"
        )

settings = Settings()