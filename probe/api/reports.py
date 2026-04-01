"""API routes for generating reports and comparisons."""

from fastapi import APIRouter, HTTPException
from sqlmodel import select

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _load_result_dicts(run_id: int, session) -> list[dict]:
    from probe.db.models import TestCase, TestResult

    cases = list(session.exec(select(TestCase).where(TestCase.run_id == run_id)).all())
    case_map = {c.id: c for c in cases}
    case_ids = [c.id for c in cases]
    results_raw = list(session.exec(
        select(TestResult).where(TestResult.test_case_id.in_(case_ids))
    ).all())
    return [
        {
            "pressure_level": case_map[r.test_case_id].pressure_level,
            "claim_type": case_map[r.test_case_id].claim_type,
            "is_control": case_map[r.test_case_id].is_control,
            "score": r.score,
            "confidence": r.confidence,
            "response_time_ms": r.response_time_ms,
        }
        for r in results_raw if r.test_case_id in case_map
    ]


@router.get("/{run_id}")
async def get_report(run_id: int) -> dict:
    """Generate a sycophancy report for a completed run."""
    from probe.db import init_db, get_session
    from probe.db.models import TestRun as TestRunModel
    from probe.analysis.curves import build_report

    init_db()
    with get_session() as session:
        run = session.get(TestRunModel, run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        result_dicts = _load_result_dicts(run_id, session)
        date = run.created_at.strftime("%Y-%m-%d")
        model = run.target_model

    return build_report(result_dicts, model=model, date=date)


@router.get("/compare/{run_a}/{run_b}")
async def compare_runs(run_a: int, run_b: int) -> dict:
    """Compare sycophancy curves between two runs."""
    from probe.db import init_db, get_session
    from probe.db.models import TestRun as TestRunModel
    from probe.analysis.curves import compute_sycophancy_curve, find_break_point

    init_db()
    with get_session() as session:
        run_a_rec = session.get(TestRunModel, run_a)
        run_b_rec = session.get(TestRunModel, run_b)
        if not run_a_rec:
            raise HTTPException(status_code=404, detail=f"Run {run_a} not found")
        if not run_b_rec:
            raise HTTPException(status_code=404, detail=f"Run {run_b} not found")

        results_a = _load_result_dicts(run_a, session)
        results_b = _load_result_dicts(run_b, session)

    curve_a = compute_sycophancy_curve(results_a)
    curve_b = compute_sycophancy_curve(results_b)

    return {
        "run_a": {
            "id": run_a,
            "model": run_a_rec.target_model,
            "date": run_a_rec.created_at.strftime("%Y-%m-%d"),
            "curve": curve_a,
            "break_point": find_break_point(curve_a),
        },
        "run_b": {
            "id": run_b,
            "model": run_b_rec.target_model,
            "date": run_b_rec.created_at.strftime("%Y-%m-%d"),
            "curve": curve_b,
            "break_point": find_break_point(curve_b),
        },
        "delta": [round(b - a, 4) for a, b in zip(curve_a, curve_b)],
    }
