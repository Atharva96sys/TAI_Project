"""
MedTrust-Engine: Review Queue Manager (Slice 3)
Human-in-the-loop oversight state machine for escalated clinical queries.

States:
  PENDING   → Newly enqueued, awaiting clinician review.
  UNDER_REVIEW → Assigned to a clinician, review in progress.
  APPROVED  → Clinician confirmed AI response is safe.
  REJECTED  → Clinician overrode AI response (incorrect/unsafe).
  ESCALATED → Requires multi-disciplinary team review (high-risk contradiction).
  DISMISSED → Non-clinical junk query, dismissed without clinical review.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.review import ReviewQueueItem


# ──────────────────────────────────────────────────────────────────────────────
# State Machine Constants
# ──────────────────────────────────────────────────────────────────────────────

STATE_PENDING = "PENDING"
STATE_UNDER_REVIEW = "UNDER_REVIEW"
STATE_APPROVED = "APPROVED"
STATE_REJECTED = "REJECTED"
STATE_ESCALATED = "ESCALATED"
STATE_DISMISSED = "DISMISSED"

VALID_STATES = {
    STATE_PENDING,
    STATE_UNDER_REVIEW,
    STATE_APPROVED,
    STATE_REJECTED,
    STATE_ESCALATED,
    STATE_DISMISSED,
}

# Valid state transitions: {current_state: {allowed_next_states}}
TRANSITION_MAP: dict[str, set[str]] = {
    STATE_PENDING: {STATE_UNDER_REVIEW, STATE_DISMISSED, STATE_ESCALATED},
    STATE_UNDER_REVIEW: {STATE_APPROVED, STATE_REJECTED, STATE_ESCALATED},
    STATE_ESCALATED: {STATE_APPROVED, STATE_REJECTED},
    STATE_APPROVED: set(),   # terminal
    STATE_REJECTED: set(),   # terminal
    STATE_DISMISSED: set(),  # terminal
}


class ReviewQueueManager:
    """
    Manages the MedTrust Review Queue Dock — the human oversight station.
    Handles enqueue, state transitions, and query/audit operations.
    """

    @staticmethod
    async def enqueue(
        session: AsyncSession,
        query_id: str,
        response_id: str | None,
        risk_tier: str,
        review_reason: str,
        trust_profile_summary: str,
        is_auto_routed: bool = True,
    ) -> ReviewQueueItem:
        """
        Enqueue a query/response for human clinical review.

        Args:
            session: Active async DB session.
            query_id: The originating QRY-* ID.
            response_id: The RSP-* ID if a response was generated (None if BLOCKED).
            risk_tier: The risk tier that triggered the review requirement.
            review_reason: Human-readable reason for escalation.
            trust_profile_summary: JSON-serializable summary of the Trust Profile.
            is_auto_routed: True if auto-triggered by Risk Engine, False if manual.

        Returns:
            The newly created ReviewQueueItem ORM instance.
        """
        item = ReviewQueueItem(
            query_id=query_id,
            response_id=response_id,
            risk_tier=risk_tier,
            review_reason=review_reason,
            trust_profile_summary=trust_profile_summary,
            status=STATE_PENDING,
            is_auto_routed=is_auto_routed,
            enqueued_at=datetime.now(timezone.utc),
        )
        session.add(item)
        await session.flush()
        return item

    @staticmethod
    async def transition(
        session: AsyncSession,
        item_id: str,
        new_state: str,
        reviewer_id: str | None = None,
        reviewer_notes: str | None = None,
    ) -> ReviewQueueItem:
        """
        Advance a ReviewQueueItem through the oversight state machine.

        Args:
            session: Active async DB session.
            item_id: The RVW-* queue item ID.
            new_state: Target state to transition to.
            reviewer_id: Clinician/reviewer identifier.
            reviewer_notes: Optional review decision rationale.

        Returns:
            Updated ReviewQueueItem.

        Raises:
            ValueError: If transition is invalid or item not found.
        """
        if new_state not in VALID_STATES:
            raise ValueError(f"Invalid review state: '{new_state}'. Must be one of {VALID_STATES}.")

        result = await session.execute(
            select(ReviewQueueItem).where(ReviewQueueItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise ValueError(f"ReviewQueueItem '{item_id}' not found.")

        allowed = TRANSITION_MAP.get(item.status, set())
        if new_state not in allowed:
            raise ValueError(
                f"Invalid transition: '{item.status}' → '{new_state}'. "
                f"Allowed from '{item.status}': {allowed or 'none (terminal state)'}."
            )

        item.status = new_state
        if reviewer_id:
            item.reviewer_id = reviewer_id
        if reviewer_notes:
            item.reviewer_notes = reviewer_notes
        item.reviewed_at = datetime.now(timezone.utc)

        await session.flush()
        return item

    @staticmethod
    async def get_queue(
        session: AsyncSession,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReviewQueueItem]:
        """
        Retrieve paginated Review Queue items, optionally filtered by state.

        Args:
            session: Active async DB session.
            status_filter: Optional state to filter by (e.g. 'PENDING').
            limit: Max records to return.
            offset: Pagination offset.

        Returns:
            List of ReviewQueueItem instances ordered by enqueued_at descending.
        """
        stmt = (
            select(ReviewQueueItem)
            .options(selectinload(ReviewQueueItem.query))
        )
        if status_filter:
            stmt = stmt.where(ReviewQueueItem.status == status_filter)
        stmt = stmt.order_by(ReviewQueueItem.enqueued_at.desc()).limit(limit).offset(offset)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_item(
        session: AsyncSession,
        item_id: str,
    ) -> ReviewQueueItem | None:
        """Fetch a single ReviewQueueItem by ID."""
        result = await session.execute(
            select(ReviewQueueItem)
            .where(ReviewQueueItem.id == item_id)
            .options(selectinload(ReviewQueueItem.query))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_queue_stats(session: AsyncSession) -> dict[str, int]:
        """Return count of items per state for dashboard telemetry."""
        from sqlalchemy import func
        result = await session.execute(
            select(ReviewQueueItem.status, func.count(ReviewQueueItem.id))
            .group_by(ReviewQueueItem.status)
        )
        return {row[0]: row[1] for row in result.all()}
