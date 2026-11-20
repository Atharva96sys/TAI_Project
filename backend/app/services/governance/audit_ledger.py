import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit import AuditEvent


class CryptographicAuditLedger:
    """Tamper-evident, cryptographically chained rolling SHA-256 audit ledger."""

    GENESIS_HASH = "0" * 64

    @classmethod
    def compute_sha256(cls, data: str) -> str:
        """Calculate SHA-256 cryptographic hex digest."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @classmethod
    async def get_latest_chain_hash(cls, session: AsyncSession) -> str:
        """Fetch the most recent audit chain hash or return genesis hash if empty."""
        stmt = select(AuditEvent.current_chain_hash).order_by(desc(AuditEvent.created_at)).limit(1)
        res = await session.execute(stmt)
        latest = res.scalar_one_or_none()
        return latest or cls.GENESIS_HASH

    @classmethod
    async def append_event(
        cls,
        session: AsyncSession,
        event_type: str,
        actor_id: str = "SYSTEM",
        payload: dict | None = None,
        query_id: str | None = None,
        document_id: str | None = None,
    ) -> AuditEvent:
        """Append a new tamper-evident event to the rolling hash chain."""
        payload_data = payload or {}
        canonical_payload = json.dumps(payload_data, sort_keys=True)
        payload_hash = cls.compute_sha256(canonical_payload)

        prev_hash = await cls.get_latest_chain_hash(session)
        now_str = datetime.now(timezone.utc).isoformat()

        # Chain Hash = SHA256(prev_chain_hash + payload_hash + timestamp)
        chain_input = f"{prev_hash}:{payload_hash}:{now_str}"
        current_hash = cls.compute_sha256(chain_input)

        entry = AuditEvent(
            event_type=event_type,
            actor_id=actor_id,
            query_id=query_id,
            document_id=document_id,
            payload_json=canonical_payload,
            payload_hash=payload_hash,
            prev_chain_hash=prev_hash,
            current_chain_hash=current_hash,
        )
        session.add(entry)
        await session.flush()
        return entry

    @classmethod
    async def verify_chain_integrity(cls, session: AsyncSession) -> dict:
        """Verify unbroken cryptographic integrity across all chronological audit records."""
        stmt = select(AuditEvent).order_by(AuditEvent.created_at.asc())
        res = await session.execute(stmt)
        events = res.scalars().all()

        if not events:
            return {
                "is_valid": True,
                "total_records": 0,
                "genesis_hash": cls.GENESIS_HASH,
                "latest_hash": cls.GENESIS_HASH,
                "message": "Audit ledger is currently empty (Genesis state).",
            }

        expected_prev = cls.GENESIS_HASH
        for idx, ev in enumerate(events):
            # 1. Check prev_chain_hash matches expected preceding hash
            if ev.prev_chain_hash != expected_prev:
                return {
                    "is_valid": False,
                    "total_records": len(events),
                    "violation_index": idx,
                    "event_id": ev.id,
                    "expected_prev": expected_prev,
                    "actual_prev": ev.prev_chain_hash,
                    "message": f"Cryptographic link broken at record index {idx} (ID: {ev.id}).",
                }

            # 2. Check payload hash matches stored canonical payload
            recalculated_payload_hash = cls.compute_sha256(ev.payload_json)
            if recalculated_payload_hash != ev.payload_hash:
                return {
                    "is_valid": False,
                    "total_records": len(events),
                    "violation_index": idx,
                    "event_id": ev.id,
                    "message": f"Payload tampering detected at record index {idx} (ID: {ev.id}).",
                }

            expected_prev = ev.current_chain_hash

        return {
            "is_valid": True,
            "total_records": len(events),
            "genesis_hash": cls.GENESIS_HASH,
            "latest_hash": events[-1].current_chain_hash,
            "message": f"All {len(events)} cryptographic chain links verified intact.",
        }

    @classmethod
    async def export_audit_records(cls, session: AsyncSession, export_format: str = "json") -> str:
        """Export full audit ledger in JSON or CSV format."""
        stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc())
        res = await session.execute(stmt)
        records = res.scalars().all()

        if export_format.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "ID", "Timestamp (UTC)", "Event Type", "Actor ID", "Query ID",
                "Document ID", "Payload Hash", "Prev Chain Hash", "Current Chain Hash"
            ])
            for r in records:
                writer.writerow([
                    r.id, r.created_at.isoformat(), r.event_type, r.actor_id,
                    r.query_id or "", r.document_id or "", r.payload_hash,
                    r.prev_chain_hash, r.current_chain_hash
                ])
            return output.getvalue()

        # Default JSON format
        data = [
            {
                "id": r.id,
                "timestamp": r.created_at.isoformat(),
                "event_type": r.event_type,
                "actor_id": r.actor_id,
                "query_id": r.query_id,
                "document_id": r.document_id,
                "payload_json": r.payload_json,
                "payload_hash": r.payload_hash,
                "prev_chain_hash": r.prev_chain_hash,
                "current_chain_hash": r.current_chain_hash,
            }
            for r in records
        ]
        return json.dumps(data, indent=2)
