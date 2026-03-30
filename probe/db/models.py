"""SQLModel table definitions for Probe."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TestRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    target_model: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"
    config: str = "{}"
    total_tests: int = 0
    completed_tests: int = 0


class TestCase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="testrun.id")
    claim_type: str
    claim_text: str
    ground_truth: str
    false_value: str
    pressure_level: int
    pressure_template: str
    conversation_context: str = ""
    is_control: bool = False
    generation: int = 0


class TestResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    test_case_id: int = Field(foreign_key="testcase.id")
    model_response: str
    score: str
    confidence: str = "high"
    contains_ground_truth: bool = False
    contains_false_value: bool = False
    hedging_signals: str = "[]"
    response_time_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "eval"   # "eval", "canary", "borderline"
    model_id: str = ""     # denormalized for faster queries


class SubjectiveTestGroup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="testrun.id")
    content: str
    content_type: str


class SubjectiveTestCase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="subjectivetestgroup.id")
    attribution: str
    attribution_level: str
    framing_text: str
    model_response: str = ""
    bias_score: float = 0.0
    sentiment_score: float = 0.0


class EvolutionRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    generation: int
    test_case_id: int = Field(foreign_key="testcase.id")
    parent_test_case_id: Optional[int] = None
    mutation_type: str
    fitness_score: float = 0.0
