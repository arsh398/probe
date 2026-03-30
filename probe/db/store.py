"""CRUD operations for all database models."""

import json
from datetime import datetime

from sqlmodel import Session, select

from probe.db.models import (
    EvolutionRecord,
    SubjectiveTestCase,
    SubjectiveTestGroup,
    TestCase,
    TestResult,
    TestRun,
)


# ---------------------------------------------------------------------------
# TestRun
# ---------------------------------------------------------------------------

def create_run(session: Session, target_model: str, config: dict) -> TestRun:
    run = TestRun(target_model=target_model, config=json.dumps(config))
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def get_run(session: Session, run_id: int) -> TestRun | None:
    return session.get(TestRun, run_id)


def list_runs(session: Session, limit: int = 50) -> list[TestRun]:
    return list(session.exec(select(TestRun).order_by(TestRun.created_at.desc()).limit(limit)).all())


def update_run_status(session: Session, run_id: int, status: str) -> None:
    run = session.get(TestRun, run_id)
    if run:
        run.status = status
        session.add(run)
        session.commit()


def increment_completed(session: Session, run_id: int) -> None:
    run = session.get(TestRun, run_id)
    if run:
        run.completed_tests += 1
        session.add(run)
        session.commit()


# ---------------------------------------------------------------------------
# TestCase
# ---------------------------------------------------------------------------

def create_test_cases(session: Session, cases: list[dict]) -> list[TestCase]:
    db_cases = [TestCase(**c) for c in cases]
    session.add_all(db_cases)
    session.commit()
    for c in db_cases:
        session.refresh(c)
    return db_cases


def get_cases_for_run(session: Session, run_id: int) -> list[TestCase]:
    return list(session.exec(select(TestCase).where(TestCase.run_id == run_id)).all())


def get_cases_by_generation(session: Session, run_id: int, generation: int) -> list[TestCase]:
    return list(
        session.exec(
            select(TestCase)
            .where(TestCase.run_id == run_id)
            .where(TestCase.generation == generation)
        ).all()
    )


# ---------------------------------------------------------------------------
# TestResult
# ---------------------------------------------------------------------------

def create_result(session: Session, result: dict) -> TestResult:
    db_result = TestResult(**result)
    session.add(db_result)
    session.commit()
    session.refresh(db_result)
    return db_result


def get_results_for_run(session: Session, run_id: int) -> list[TestResult]:
    """Join through TestCase to get results for a run."""
    cases = get_cases_for_run(session, run_id)
    case_ids = {c.id for c in cases}
    return list(
        session.exec(
            select(TestResult).where(TestResult.test_case_id.in_(case_ids))
        ).all()
    )


def get_results_by_pressure_level(
    session: Session, run_id: int, level: int
) -> list[TestResult]:
    cases = session.exec(
        select(TestCase)
        .where(TestCase.run_id == run_id)
        .where(TestCase.pressure_level == level)
    ).all()
    case_ids = {c.id for c in cases}
    return list(
        session.exec(
            select(TestResult).where(TestResult.test_case_id.in_(case_ids))
        ).all()
    )


# ---------------------------------------------------------------------------
# SubjectiveTestGroup / SubjectiveTestCase
# ---------------------------------------------------------------------------

def create_subjective_group(session: Session, run_id: int, content: str, content_type: str) -> SubjectiveTestGroup:
    group = SubjectiveTestGroup(run_id=run_id, content=content, content_type=content_type)
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def create_subjective_case(session: Session, case: dict) -> SubjectiveTestCase:
    db_case = SubjectiveTestCase(**case)
    session.add(db_case)
    session.commit()
    session.refresh(db_case)
    return db_case


# ---------------------------------------------------------------------------
# EvolutionRecord
# ---------------------------------------------------------------------------

def create_evolution_record(session: Session, record: dict) -> EvolutionRecord:
    db_record = EvolutionRecord(**record)
    session.add(db_record)
    session.commit()
    session.refresh(db_record)
    return db_record


def get_elite_cases(session: Session, run_id: int, top_fraction: float = 0.2) -> list[tuple[TestCase, float]]:
    """
    Return (TestCase, fitness_score) pairs for the top fraction of cases,
    sorted by fitness descending.
    """
    from probe.evolution.fitness import calculate_fitness

    cases = get_cases_for_run(session, run_id)
    scored = []
    for case in cases:
        results = list(
            session.exec(
                select(TestResult).where(TestResult.test_case_id == case.id)
            ).all()
        )
        if results:
            avg_fitness = sum(calculate_fitness(r.score) for r in results) / len(results)
            scored.append((case, avg_fitness))

    scored.sort(key=lambda x: x[1], reverse=True)
    cutoff = max(1, int(len(scored) * top_fraction))
    return scored[:cutoff]
