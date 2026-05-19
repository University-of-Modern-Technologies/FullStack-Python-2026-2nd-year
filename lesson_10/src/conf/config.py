from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


def _split_csv(value: str) -> list[str]:
    if not value or not value.strip():
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


class Settings(BaseSettings):
    DB_URL: str = "postgresql+asyncpg://user:password@localhost:5432/todo_app"
    JWT_SECRET_KEY: str = "dev-secret-change-me-32-bytes-minimum"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:5500"

    # --- rate limiting ---
    RATE_LIMIT_ME: str = "10/minute"

    # --- кеш todos ---
    CACHE_TTL_SECONDS: int = 60

    # --- IP blacklist (JSON) ---
    BLOCKED_IPS_FILE: str = "data/blocked_ips.json"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return _split_csv(self.CORS_ORIGINS)

    @property
    def blocked_ips_path(self) -> Path:
        path = Path(self.BLOCKED_IPS_FILE)
        if path.is_absolute():
            return path
        return BASE_DIR / path


settings = Settings()
