from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PrivacyEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: str
    source_id: str | None = None
    entity_type: str
    masked_snippet: str
    redacted_token: str
    created_at: datetime


class PrivacyScanRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Clinical text to scan and pseudonymize")


class RedactedEntityRead(BaseModel):
    entity_type: str
    original_value: str
    token: str
    start_char: int
    end_char: int


class PrivacyScanResponse(BaseModel):
    has_pii: bool
    total_redactions: int
    raw_text: str
    protected_text: str
    entities_detected: list[RedactedEntityRead]
    token_map: dict[str, str]


class PrivacyStatsResponse(BaseModel):
    total_events: int
    total_mrns_masked: int
    total_names_masked: int
    total_dates_masked: int
    total_contacts_masked: int
