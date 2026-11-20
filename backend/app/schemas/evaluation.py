from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EvaluationCaseResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    case_category: str
    query_text: str
    expected_status: str
    actual_status: str
    passed: bool
    latency_ms: float
    metrics_json: str
    created_at: datetime


class EvaluationRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_name: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    mean_evidence_coverage: float
    mean_grounding_accuracy: float
    injection_detection_rate: float
    pii_recall: float
    refusal_f1: float
    mean_latency_ms: float
    created_at: datetime
    case_results: list[EvaluationCaseResultRead] = []


class TriggerBenchmarkRequest(BaseModel):
    run_name: str = "Automated Lab Benchmark"
