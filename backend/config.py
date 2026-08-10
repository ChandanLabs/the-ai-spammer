from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always resolve .env relative to this file (backend/.env), regardless of CWD
_ENV_FILE = Path(__file__).parent / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@db.yourproject.supabase.co:5432/postgres"
    TELEGRAM_BOT_TOKEN: str = ""
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    NUDGE_INTERVAL_MINUTES: int = 30
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Auth ─────────────────────────────────────────────────
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "changeme123"   # override in .env!
    JWT_SECRET: str = "super-secret-jwt-key-change-this" # override in .env!
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480          # 8 hours

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
