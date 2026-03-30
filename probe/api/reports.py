"""API routes for generating reports."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{run_id}")
async def get_report(run_id: int, format: str = "json") -> dict:
    """Generate a sycophancy report for a completed run. (Implemented in Week 4)"""
    raise HTTPException(status_code=501, detail="Reports not yet implemented (Week 4)")


@router.get("/compare/{run_a}/{run_b}")
async def compare_runs(run_a: int, run_b: int) -> dict:
    """Compare sycophancy curves between two runs. (Implemented in Week 4)"""
    raise HTTPException(status_code=501, detail="Comparison not yet implemented (Week 4)")
