from fastapi import APIRouter, Depends, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.security import SecurityEvent
from backend.app.schemas.security import (
    SecurityEventRead,
    SecurityScanQueryRequest,
    SecurityScanResponse,
    SecurityStatsResponse,
)
from backend.app.services.security.airlock import SecurityAirlock

router = APIRouter(prefix="/security", tags=["Security Airlock"])


@router.post("/scan-query", response_model=SecurityScanResponse, summary="Screen prompt for prompt injection")
async def scan_query(req: SecurityScanQueryRequest, db: AsyncSession = Depends(get_db)):
    res = SecurityAirlock.scan_query(req.query)
    if not res.is_safe:
        await SecurityAirlock.log_security_event(
            session=db,
            event_type="DIRECT_INJECTION",
            threat_level=res.threat_level,
            source_type="QUERY",
            detected_pattern=res.detected_pattern or req.query[:100],
            action_taken=res.action_taken,
        )
        await db.commit()

    return SecurityScanResponse(
        is_safe=res.is_safe,
        threat_category=res.threat_category,
        threat_level=res.threat_level,
        detected_pattern=res.detected_pattern,
        sanitized_text=res.sanitized_text,
        action_taken=res.action_taken,
    )


@router.get("/events", response_model=list[SecurityEventRead], summary="List all security events")
async def get_security_events(limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(SecurityEvent).order_by(desc(SecurityEvent.created_at)).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/stats", response_model=SecurityStatsResponse, summary="Aggregated security metrics")
async def get_security_stats(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count(SecurityEvent.id))) or 0
    direct = await db.scalar(
        select(func.count(SecurityEvent.id)).where(SecurityEvent.event_type == "DIRECT_INJECTION")
    ) or 0
    indirect = await db.scalar(
        select(func.count(SecurityEvent.id)).where(SecurityEvent.event_type == "INDIRECT_INJECTION")
    ) or 0
    quarantined = await db.scalar(
        select(func.count(SecurityEvent.id)).where(SecurityEvent.action_taken == "QUARANTINED")
    ) or 0
    blocked = await db.scalar(
        select(func.count(SecurityEvent.id)).where(SecurityEvent.action_taken == "BLOCKED")
    ) or 0

    return SecurityStatsResponse(
        total_events=total,
        direct_injections_caught=direct,
        indirect_injections_caught=indirect,
        quarantined_documents=quarantined,
        blocked_queries=blocked,
    )
