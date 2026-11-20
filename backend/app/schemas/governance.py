from pydantic import BaseModel


class NistControlItem(BaseModel):
    nist_function: str
    control_id: str
    medtrust_mechanism: str
    status: str
    metric_value: str


class GovernanceMetricsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_queries: int
    verified_queries: int
    partially_verified_queries: int
    insufficient_evidence_queries: int
    review_required_queries: int
    blocked_queries: int
    mean_evidence_coverage_pct: float
    mean_grounding_score: float
    mean_latency_ms: float
    total_security_events: int
    total_privacy_events: int
    total_audit_records: int
    chain_integrity_valid: bool
    nist_controls: list[NistControlItem]
