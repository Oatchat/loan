from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from .config import settings
from .db import engine, init_db
from .models import User
from .routers import auth, debtors, payments, attachments, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    # Auto-seed demo data if DB is empty (e.g. fresh deploy on ephemeral disk)
    with Session(engine) as s:
        has_user = s.exec(select(User)).first()
        if not has_user:
            from .seed import run as run_seed
            try:
                run_seed()
            except Exception as e:
                print(f"⚠ auto-seed failed: {e}")
    yield


app = FastAPI(
    title="DebtTrack API",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)


def _cors_origins() -> list[str]:
    """Origins list with wildcard support for *.vercel.app preview deploys."""
    return settings.cors_origin_list


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(debtors.router)
app.include_router(debtors.calc_router)
app.include_router(payments.router)
app.include_router(attachments.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {"name": "DebtTrack API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
