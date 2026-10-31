from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEVELOPMENT_SIGNING_KEY = "development-only-change-this-key-before-deploying"


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str | None = None
    session_signing_key: str = DEVELOPMENT_SIGNING_KEY
    frontend_origin: str = "http://localhost:5173"
    upload_dir: str = "backend/var/private_uploads"
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    tavily_api_key: str | None = None
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    max_upload_bytes: int = 20 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    @property
    def cookie_secure(self) -> bool:
        return self.app_env.casefold() == "production"

    @property
    def frontend_origins(self) -> list[str]:
        configured = [value.strip().rstrip("/") for value in self.frontend_origin.split(",") if value.strip()]
        origins: list[str] = []
        for origin in configured:
            if origin not in origins:
                origins.append(origin)

            if self.app_env.casefold() != "development":
                continue

            parsed = urlsplit(origin)
            if parsed.hostname not in {"localhost", "127.0.0.1"}:
                continue

            ports = [parsed.port]
            if parsed.port in {4173, 5173}:
                ports.extend([4173, 5173])
            for host in {"localhost", "127.0.0.1"}:
                for port in ports:
                    authority = f"{host}:{port}" if port else host
                    alias = urlunsplit((parsed.scheme, authority, parsed.path, parsed.query, parsed.fragment)).rstrip("/")
                    if alias not in origins:
                        origins.append(alias)
        return origins

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        return path if path.is_absolute() else (BACKEND_DIR.parent / path).resolve()


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.app_env.casefold() == "production":
        signing_key = settings.session_signing_key.strip()
        placeholders = {DEVELOPMENT_SIGNING_KEY, "replace-with-at-least-32-random-bytes"}
        if len(signing_key) < 32 or signing_key in placeholders or signing_key.casefold().startswith("replace-with-"):
            raise ValueError("SESSION_SIGNING_KEY must be at least 32 characters and must not be a placeholder in production.")
        settings.session_signing_key = signing_key
    return settings
