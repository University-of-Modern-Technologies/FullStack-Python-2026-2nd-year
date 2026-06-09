"""Налаштування застосунку, що завантажуються з .env."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


def _split_csv(value: str) -> list[str]:
    """Перетворює CSV-рядок з налаштувань на список непорожніх значень."""
    if not value or not value.strip():
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


class Settings(BaseSettings):
    """Описує всі змінні конфігурації застосунку."""
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

    EMAIL_TOKEN_SECRET_KEY: str = "dev-email-token-secret-change-me"
    EMAIL_VERIFY_EXPIRE_HOURS: int = 24
    APP_PUBLIC_URL: str = "http://127.0.0.1:8000"

    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@example.com"
    MAIL_FROM_NAME: str = "Todo API"
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_VALIDATE_CERTS: bool = True

    CLD_NAME: str = ""
    CLD_API_KEY: str = ""
    CLD_API_SECRET: str = ""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Повертає дозволені CORS origins як список рядків."""
        return _split_csv(self.CORS_ORIGINS)

    @property
    def blocked_ips_path(self) -> Path:
        """Повертає абсолютний шлях до JSON-файлу заблокованих IP."""
        path = Path(self.BLOCKED_IPS_FILE)
        if path.is_absolute():
            return path
        return BASE_DIR / path

    @property
    def template_folder(self) -> Path:
        """Повертає шлях до папки email-шаблонів."""
        return BASE_DIR / "src" / "templates" / "email"

    @property
    def templates_dir(self) -> Path:
        """Повертає шлях до кореневої папки HTML-шаблонів."""
        return BASE_DIR / "src" / "templates"


settings = Settings()
