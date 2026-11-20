from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SecurityEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    threat_level: str
    source_type: str
    source_id: str | None = None
    detected_pattern: str
    action_taken: str
    created_at: datetime


class SecurityScanQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Clinical query to screen for prompt injection")


class SecurityScanResponse(BaseModel):
    is_safe: bool
    threat_category: str | None = None
    threat_level: str
    detected_pattern: str | None = None
    sanitized_text: str
    action_taken: str


class SecurityStatsResponse(BaseModel):
    total_events: int
    direct_injections_caught: int
    indirect_injections_caught: int
    quarantined_documents: int
    blocked_queries: int
