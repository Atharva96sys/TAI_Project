from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.security import PrivacyEvent
from backend.app.schemas.privacy import (
    PrivacyEventRead,
    PrivacyScanRequest,
    PrivacyScanResponse,
    PrivacyStatsResponse,
    RedactedEntityRead,
)
from backend.app.services.privacy.shield import PrivacyShield

router = APIRouter(prefix="/privacy", tags=["Privacy Shield"])


@router.post("/scan-text", response_model=PrivacyScanResponse, summary="Scan text and apply HIPAA Safe Harbor pseudonymization")
async def scan_text(req: PrivacyScanRequest, db: AsyncSession = Depends(get_db)):
    res = PrivacyShield.scan_and_pseudonymize(req.text)
    if res.has_pii:
        await PrivacyShield.log_privacy_events(
            session=db,
            source_type="API_SCAN",
            entities=res.entities_detected,
        )
        await db.commit()

    return PrivacyScanResponse(
        has_pii=res.has_pii,
        total_redactions=res.total_redactions,
        raw_text=req.text,
        protected_text=res.protected_text,
        entities_detected=[
            RedactedEntityRead(
                entity_type=e.entity_type,
                original_value=e.original_value,
                token=e.token,
                start_char=e.start_char,
                end_char=e.end_char,
            )
            for e in res.entities_detected
        ],
        token_map=res.token_map,
    )


@router.get("/events", response_model=list[PrivacyEventRead], summary="List recorded privacy events")
async def get_privacy_events(limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(PrivacyEvent).order_by(desc(PrivacyEvent.created_at)).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/stats", response_model=PrivacyStatsResponse, summary="Aggregated privacy metrics")
async def get_privacy_stats(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count(PrivacyEvent.id))) or 0
    mrns = await db.scalar(
        select(func.count(PrivacyEvent.id)).where(PrivacyEvent.entity_type == "MRN")
    ) or 0
    names = await db.scalar(
        select(func.count(PrivacyEvent.id)).where(PrivacyEvent.entity_type == "PATIENT_NAME")
    ) or 0
    dates = await db.scalar(
        select(func.count(PrivacyEvent.id)).where(PrivacyEvent.entity_type.in_(["DATE_OF_BIRTH", "DATE"]))
    ) or 0
    contacts = await db.scalar(
        select(func.count(PrivacyEvent.id)).where(PrivacyEvent.entity_type.in_(["PHONE", "EMAIL", "ADDRESS"]))
    ) or 0

    return PrivacyStatsResponse(
        total_events=total,
        total_mrns_masked=mrns,
        total_names_masked=names,
        total_dates_masked=dates,
        total_contacts_masked=contacts,
    )
