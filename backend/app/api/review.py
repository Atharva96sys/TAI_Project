"""
MedTrust-Engine: Review Queue Dock API (Slice 3)
Human-in-the-loop clinical oversight station.

Endpoints:
  GET  /api/review/queue          — List review queue (filterable by status)
  GET  /api/review/queue/stats    — Operational stats for dashboard
  GET  /api/review/queue/{id}     — Fetch single queue item
  POST /api/review/queue/{id}/transition — Advance state machine
  POST /api/review/queue/{id}/escalate   — Escalate to multi-disciplinary review
"""
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.schemas.risk import (
    ReviewQueueItemRead,
    ReviewQueueListResponse,
    ReviewQueueStatsResponse,
    ReviewTransitionRequest,
)
from backend.app.services.risk.review_queue import ReviewQueueManager

router = APIRouter(prefix="/review", tags=["Review Queue Dock — Human Oversight"])


@router.get(
    "/queue",
    response_model=ReviewQueueListResponse,
    summary="List Review Queue items with optional state filter",
)
async def list_review_queue(
    status: str | None = QueryParam(
        None,
        pattern="^(PENDING|UNDER_REVIEW|APPROVED|REJECTED|ESCALATED|DISMISSED)$",
        description="Filter by review state",
    ),
    limit: int = QueryParam(50, ge=1, le=200),
    offset: int = QueryParam(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a paginated list of Review Queue items.
    Supports filtering by operational status (PENDING, UNDER_REVIEW, etc.).
    """
    items = await ReviewQueueManager.get_queue(
        session=db,
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    stats = await ReviewQueueManager.get_queue_stats(db)
    return ReviewQueueListResponse(
        items=[ReviewQueueItemRead.model_validate(i) for i in items],
        total_shown=len(items),
        status_filter=status,
        stats=stats,
    )


@router.get(
    "/queue/stats",
    response_model=ReviewQueueStatsResponse,
    summary="Review Queue operational statistics for governance dashboard",
)
async def get_queue_stats(db: AsyncSession = Depends(get_db)):
    """
    Returns count of review queue items per state.
    Used by the Governance Dashboard for live telemetry.
    """
    stats = await ReviewQueueManager.get_queue_stats(db)
    return ReviewQueueStatsResponse(
        pending=stats.get("PENDING", 0),
        under_review=stats.get("UNDER_REVIEW", 0),
        approved=stats.get("APPROVED", 0),
        rejected=stats.get("REJECTED", 0),
        escalated=stats.get("ESCALATED", 0),
        dismissed=stats.get("DISMISSED", 0),
        total=sum(stats.values()),
    )


@router.get(
    "/queue/{item_id}",
    response_model=ReviewQueueItemRead,
    summary="Fetch a single Review Queue item by ID",
)
async def get_review_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single ReviewQueueItem by its RVW-* ID."""
    item = await ReviewQueueManager.get_item(session=db, item_id=item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review queue item '{item_id}' not found.",
        )
    return ReviewQueueItemRead.model_validate(item)


@router.post(
    "/queue/{item_id}/transition",
    response_model=ReviewQueueItemRead,
    summary="Advance a Review Queue item through the clinical oversight state machine",
)
async def transition_review_item(
    item_id: str,
    req: ReviewTransitionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Transition a ReviewQueueItem to the next state.

    Valid transitions:
    - PENDING → UNDER_REVIEW | DISMISSED | ESCALATED
    - UNDER_REVIEW → APPROVED | REJECTED | ESCALATED
    - ESCALATED → APPROVED | REJECTED

    APPROVED and REJECTED are terminal states.
    """
    try:
        item = await ReviewQueueManager.transition(
            session=db,
            item_id=item_id,
            new_state=req.new_state,
            reviewer_id=req.reviewer_id,
            reviewer_notes=req.reviewer_notes,
        )
        await db.commit()
        return ReviewQueueItemRead.model_validate(item)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/queue/{item_id}/escalate",
    response_model=ReviewQueueItemRead,
    summary="Escalate a Review Queue item to multi-disciplinary team review",
)
async def escalate_review_item(
    item_id: str,
    reviewer_id: str = QueryParam(..., description="Clinician escalating the case"),
    escalation_reason: str = QueryParam(..., max_length=2000, description="Clinical justification for escalation"),
    db: AsyncSession = Depends(get_db),
):
    """
    Fast-track escalation path — transition PENDING or UNDER_REVIEW → ESCALATED
    with a required escalation justification.
    """
    try:
        item = await ReviewQueueManager.transition(
            session=db,
            item_id=item_id,
            new_state="ESCALATED",
            reviewer_id=reviewer_id,
            reviewer_notes=f"ESCALATION: {escalation_reason}",
        )
        await db.commit()
        return ReviewQueueItemRead.model_validate(item)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
