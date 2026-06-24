"""FastAPI application entrypoint."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import admin, lists, outreach, properties
from app.config import get_settings
from app.db import init_db

app = FastAPI(
    title="Canadian Real Estate Investment Data Platform",
    version="0.1.0",
    description="v1 scaffold — Layer C distress signals + compliance core. See README.",
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/healthz", tags=["meta"])
def healthz():
    s = get_settings()
    return {
        "status": "ok",
        "active_province": s.active_province,
        "postgis": s.is_postgis,
        "electronic_outreach_enabled": s.allow_electronic_outreach,
    }


app.include_router(properties.router)
app.include_router(lists.router)
app.include_router(outreach.router)
app.include_router(admin.router)

# Minimal map-centric demo frontend (no build step). Production target is Next.js (see docs).
_FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
if _FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND)), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(str(_FRONTEND / "index.html"))
