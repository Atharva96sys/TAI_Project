from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.audit import AuditEvent
from backend.app.schemas.audit import AuditEventRead, AuditVerificationResponse
from backend.app.services.governance.audit_ledger import CryptographicAuditLedger

router = APIRouter(prefix="/audit", tags=["Audit Ledger"])


@router.get("/events", response_model=list[AuditEventRead], summary="List cryptographic audit ledger entries")
async def get_audit_events(limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(AuditEvent).order_by(desc(AuditEvent.created_at)).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/verify", response_model=AuditVerificationResponse, summary="Verify rolling hash chain cryptographic integrity")
async def verify_chain(db: AsyncSession = Depends(get_db)):
    res = await CryptographicAuditLedger.verify_chain_integrity(db)
    return AuditVerificationResponse(
        is_valid=res["is_valid"],
        total_records=res["total_records"],
        genesis_hash=res.get("genesis_hash", CryptographicAuditLedger.GENESIS_HASH),
        latest_hash=res.get("latest_hash", CryptographicAuditLedger.GENESIS_HASH),
        message=res["message"],
        violation_index=res.get("violation_index"),
        event_id=res.get("event_id"),
    )


@router.get("/export", summary="Export audit trail in CSV or JSON format")
async def export_audit_trail(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: AsyncSession = Depends(get_db),
):
    exported_str = await CryptographicAuditLedger.export_audit_records(db, export_format=format)
    media_type = "text/csv" if format == "csv" else "application/json"
    filename = f"medtrust_audit_export.{format}"
    return Response(
        content=exported_str,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
