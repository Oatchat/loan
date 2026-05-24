from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = "dev-secret-key-change-me-please-use-long-random-string"
    access_token_expire_minutes: int = 1440
    database_url: str = "sqlite:///./debttrack.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    upload_dir: str = "./uploads"
    algorithm: str = "HS256"

    # Turso (libSQL) — when both are set, the app uses Turso instead of `database_url`.
    turso_database_url: Optional[str] = None  # e.g. libsql://loan-<user>.aws-ap-northeast-1.turso.io
    turso_auth_token: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def use_turso(self) -> bool:
        return bool(self.turso_database_url and self.turso_auth_token)

    @property
    def effective_database_url(self) -> str:
        """Pick Turso when configured, else fall back to local sqlite.

        For Turso the auth_token + secure flag are passed via SQLAlchemy
        `connect_args` (see db.py), so this URL never carries the token.
        """
        if self.use_turso:
            url = self.turso_database_url
            if url.startswith("libsql://"):
                return "sqlite+libsql://" + url[len("libsql://"):]
            if url.startswith("https://"):
                return "sqlite+libsql://" + url[len("https://"):]
            return url
        return self.database_url


settings = Settings()
