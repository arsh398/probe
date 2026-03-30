"""API routes for starting and viewing test runs."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/runs", tags=["runs"])


class StartRunRequest(BaseModel):
    model: str
    api_key: str
    claims: int = 500
    claim_types: list[str] = ["math", "logic", "science", "code"]
    control_ratio: float = 0.3


@router.post("/")
async def start_run(request: StartRunRequest) -> dict:
    """Start a new sycophancy test run. (Implemented in Week 2)"""
    raise HTTPException(status_code=501, detail="Run execution not yet implemented (Week 2)")


@router.get("/{run_id}")
async def get_run(run_id: int) -> dict:
    """Get status and results for a test run."""
    from probe.db import get_session
    from probe.db.store import get_run

    with get_session() as session:
        run = get_run(session, run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        return {
            "id": run.id,
            "target_model": run.target_model,
            "status": run.status,
            "total_tests": run.total_tests,
            "completed_tests": run.completed_tests,
            "created_at": run.created_at.isoformat(),
        }


@router.get("/")
async def list_runs(limit: int = 20) -> list[dict]:
    """List recent test runs."""
    from probe.db import get_session
    from probe.db.store import list_runs as db_list_runs

    with get_session() as session:
        runs = db_list_runs(session, limit=limit)
        return [
            {
                "id": r.id,
                "target_model": r.target_model,
                "status": r.status,
                "total_tests": r.total_tests,
                "created_at": r.created_at.isoformat(),
            }
            for r in runs
        ]
