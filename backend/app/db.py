from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine
from .config import settings


_db_url = settings.effective_database_url
_is_libsql = _db_url.startswith("sqlite+libsql://")
_is_sqlite = _db_url.startswith("sqlite")

# sqlalchemy-libsql expects auth_token + secure via connect_args, NOT URL query string.
# Local pysqlite uses check_same_thread, which libsql rejects.
connect_args: dict = {}
if _is_libsql:
    connect_args = {"auth_token": settings.turso_auth_token}
elif _is_sqlite:
    connect_args["check_same_thread"] = False

engine = create_engine(_db_url, connect_args=connect_args, echo=False)


def _migrate_user_email_to_username() -> None:
    """Rename legacy `user.email` column to `username`, and re-key the demo admin.

    Idempotent: safe to call on every startup. SQLite ≥3.25 / libsql both support RENAME COLUMN.
    """
    with engine.begin() as conn:
        tables = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user'"
        )).fetchall()
        if not tables:
            return  # fresh DB — create_all will build the new schema

        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(user)")).fetchall()]
        if "username" in cols:
            return  # already migrated
        if "email" not in cols:
            return  # unexpected shape — leave alone

        conn.execute(text("ALTER TABLE user RENAME COLUMN email TO username"))

        # Re-key the demo admin so login matches the new credentials.
        from .auth import hash_password
        new_hash = hash_password("admin")
        conn.execute(
            text("UPDATE user SET username = :u, password_hash = :p WHERE username = :old"),
            {"u": "admin", "p": new_hash, "old": "admin@debttrack.app"},
        )


def init_db() -> None:
    from . import models  # noqa: F401  ensure metadata registered
    _migrate_user_email_to_username()
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
