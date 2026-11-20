import json
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import async_session_factory, init_db
from backend.app.services.governance.audit_ledger import CryptographicAuditLedger


@pytest.mark.asyncio
async def test_cryptographic_rolling_hash_chain(test_db: AsyncSession):
    session = test_db
    # 1. Append first event (anchored to Genesis Hash)
    ev1 = await CryptographicAuditLedger.append_event(
        session=session,
        event_type="TEST_EVENT_1",
        actor_id="TEST_RUNNER",
        payload={"action": "test_genesis"},
    )
    assert ev1.prev_chain_hash == CryptographicAuditLedger.GENESIS_HASH
    assert len(ev1.current_chain_hash) == 64

    # 2. Append second event (chained to ev1)
    ev2 = await CryptographicAuditLedger.append_event(
        session=session,
        event_type="TEST_EVENT_2",
        actor_id="TEST_RUNNER",
        payload={"action": "test_chaining"},
    )
    assert ev2.prev_chain_hash == ev1.current_chain_hash
    assert ev2.current_chain_hash != ev1.current_chain_hash

    # 3. Verify Chain Integrity
    audit_status = await CryptographicAuditLedger.verify_chain_integrity(session)
    assert audit_status["is_valid"] is True
    assert audit_status["total_records"] >= 2

    # 4. Verify Export functionality
    json_export = await CryptographicAuditLedger.export_audit_records(session, "json")
    data = json.loads(json_export)
    assert isinstance(data, list)
    assert len(data) >= 2

    csv_export = await CryptographicAuditLedger.export_audit_records(session, "csv")
    assert "Prev Chain Hash" in csv_export
