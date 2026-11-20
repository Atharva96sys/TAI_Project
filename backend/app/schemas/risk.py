"""
MedTrust-Engine: Schemas for Slice 3 — Risk Engine & Review Queue API.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ──────────────────────────────────────────────────────────────────────────────
# Risk Assessment Schemas
# ──────────────────────────────────────────────────────────────────────────────

class QueryRiskAssessmentRead(BaseModel):
    """Serializable form of QueryRiskAssessment for API responses."""

    risk_tier: str
    tier_level: int
    policy: str
    pii_indicators_found: list[str] = []
    risk_flags: list[str] = []
    clinical_caveat: Optional[str] = None
    should_block: bool = False
    human_review_required: bool = False
    review_reason: Optional[str] = None
    evidence_override_triggered: bool = False


# ──────────────────────────────────────────────────────────────────────────────
# Review Queue Schemas
# ──────────────────────────────────────────────────────────────────────────────

class ReviewQueueItemRead(BaseModel):
    """Read-only schema for a ReviewQueueItem."""

    id: str
    query_id: str
    response_id: Optional[str] = None
    risk_tier: str
    review_reason: str
    trust_profile_summary: str
    status: str
    is_auto_routed: bool
    enqueued_at: datetime
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewQueueListResponse(BaseModel):
    """Paginated list of Review Queue items with metadata."""

    items: list[ReviewQueueItemRead]
    total_shown: int
    status_filter: Optional[str] = None
    stats: dict[str, int] = {}


class ReviewTransitionRequest(BaseModel):
    """Request to transition a Review Queue item to a new state."""

    new_state: str = Field(
        ...,
        pattern="^(UNDER_REVIEW|APPROVED|REJECTED|ESCALATED|DISMISSED)$",
        description="Target state for the transition",
    )
    reviewer_id: str = Field(..., min_length=2, max_length=128, description="Clinician or reviewer identifier")
    reviewer_notes: Optional[str] = Field(None, max_length=4000, description="Decision rationale or clinical notes")


class ReviewQueueStatsResponse(BaseModel):
    """Operational dashboard stats for the Review Queue Dock."""

    pending: int = 0
    under_review: int = 0
    approved: int = 0
    rejected: int = 0
    escalated: int = 0
    dismissed: int = 0
    total: int = 0
