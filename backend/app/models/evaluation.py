import uuid
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin


class EvaluationRun(Base, TimestampMixin):
    """Aggregate record of an automated benchmark execution run in the Evaluation Lab."""

    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"RUN-{uuid.uuid4().hex[:10]}"
    )
    run_name: Mapped[str] = mapped_column(String(128), nullable=False)
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    passed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Empirical Metrics
    mean_evidence_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    mean_grounding_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    injection_detection_rate: Mapped[float] = mapped_column(Float, default=0.0)
    pii_recall: Mapped[float] = mapped_column(Float, default=0.0)
    refusal_f1: Mapped[float] = mapped_column(Float, default=0.0)
    mean_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)

    case_results: Mapped[list["EvaluationCaseResult"]] = relationship(
        "EvaluationCaseResult", back_populates="run", cascade="all, delete-orphan"
    )


class EvaluationCaseResult(Base, TimestampMixin):
    """Individual scenario execution result within an evaluation run."""

    __tablename__ = "evaluation_case_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"CAS-{uuid.uuid4().hex[:10]}"
    )
    evaluation_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False
    )
    case_id: Mapped[str] = mapped_column(String(16), nullable=False)  # B01 to B10
    case_category: Mapped[str] = mapped_column(String(64), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actual_status: Mapped[str] = mapped_column(String(32), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    run: Mapped[EvaluationRun] = relationship("EvaluationRun", back_populates="case_results")
