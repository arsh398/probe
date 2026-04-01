"""FastAPI app with all routes mounted."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from probe.api.runs import router as runs_router
from probe.api.reports import router as reports_router

BASE_DIR = Path(__file__).parent.parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard" / "dist"


def create_app() -> FastAPI:
    from probe.db import init_db
    init_db()

    app = FastAPI(title="Probe API", version="0.1.0", docs_url="/api/docs")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(runs_router)
    app.include_router(reports_router)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    # Serve React dashboard if built
    if DASHBOARD_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(DASHBOARD_DIR / "assets")), name="assets")

        @app.get("/", include_in_schema=False)
        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str = "") -> FileResponse:
            return FileResponse(str(DASHBOARD_DIR / "index.html"))

    return app


app = create_app()
