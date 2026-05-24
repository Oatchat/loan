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
    def effective_database_url(self) -> str:
        """Pick Turso when configured, else fall back to local sqlite."""
        if self.turso_database_url and self.turso_auth_token:
            url = self.turso_database_url
            # SQLAlchemy + sqlalchemy-libsql dialect uses the `sqlite+libsql://` scheme.
            if url.startswith("libsql://"):
                url = "sqlite+libsql://" + url[len("libsql://"):]
            elif url.startswith("https://"):
                url = "sqlite+libsql://" + url[len("https://"):]
            sep = "&" if "?" in url else "?"
            return f"{url}{sep}authToken={self.turso_auth_token}&secure=true"
        return self.database_url


settings = Settings()
