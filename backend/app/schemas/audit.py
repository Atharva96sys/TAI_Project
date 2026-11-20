from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    actor_id: str
    query_id: str | None = None
    document_id: str | None = None
    payload_json: str
    payload_hash: str
    prev_chain_hash: str
    current_chain_hash: str
    created_at: datetime


class AuditVerificationResponse(BaseModel):
    is_valid: bool
    total_records: int
    genesis_hash: str
    latest_hash: str
    message: str
    violation_index: int | None = None
    event_id: str | None = None
