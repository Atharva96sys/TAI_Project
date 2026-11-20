import json
import time
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.document import Document, DocumentChunk, DocumentVersion
from backend.app.models.query import Query, RetrievedEvidence
from backend.app.models.verification import Claim, ClaimEvidenceLink, GeneratedResponse
from backend.app.schemas.verification import (
    ClaimEvidenceLinkRead,
    ClaimRead,
    GenerateAndVerifyRequest,
    TrustProfileRead,
    VerificationResponse,
    VerifyTextRequest,
)
from backend.app.services.generation.llm import llm_client
from backend.app.services.retrieval.engine import retrieval_engine
from backend.app.services.retrieval.provenance import ProvenanceResolver
from backend.app.services.risk.review_queue import ReviewQueueManager
from backend.app.services.risk.risk_engine import (
    POLICY_BLOCK,
    POLICY_REVIEW_REQUIRED,
    TIER_PATIENT_SPECIFIC,
    QueryRiskEngine,
)
from backend.app.services.security.airlock import SecurityAirlock
from backend.app.services.privacy.shield import PrivacyShield
from backend.app.services.governance.audit_ledger import CryptographicAuditLedger
from backend.app.services.verification.trust_engine import trust_engine

router = APIRouter(prefix="/verification", tags=["Claim Verification & Trust Engine"])


@router.post(
    "/generate-and-verify",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="End-to-end Grounded Generation, Atomic Claim Decomposition, and NLI Verification",
)
async def generate_and_verify(
    req: GenerateAndVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    total_start = time.perf_counter()

    if not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty.",
        )

    # ── STEP 0: Security Airlock Screening (Direct Prompt Injection) ────────────
    sec_scan = SecurityAirlock.scan_query(req.query)
    if not sec_scan.is_safe:
        query_id = f"QRY-SEC-{uuid.uuid4().hex[:10]}"
        total_latency_ms = (time.perf_counter() - total_start) * 1000.0
        blocked_text = (
            f"⛔ SECURITY AIRLOCK TRIGGERED: Potential adversarial injection ({sec_scan.threat_category}) "
            "detected in prompt. Execution halted to protect clinical safety boundaries."
        )
        sec_profile = TrustProfileRead(
            evidence_coverage_pct=0.0,
            mean_grounding_score=0.0,
            retrieval_quality_score=0.0,
            source_quality_tier="BLOCKED",
            contradiction_risk="LOW",
            privacy_risk="LOW",
            security_risk=f"THREAT_{sec_scan.threat_level}",
            query_risk_tier="ADVERSARIAL_INJECTION",
            uncertainty_score=1.0,
            final_status="BLOCKED",
            human_review_required=True,
        )
        query_record = Query(
            id=query_id,
            raw_query_text=req.query[:200],
            protected_query_text="[SECURITY BLOCKED]",
            query_risk_tier="ADVERSARIAL_INJECTION",
            pii_count=0,
            status="BLOCKED",
            total_latency_ms=round(total_latency_ms, 2),
        )
        db.add(query_record)
        await db.flush()

        await SecurityAirlock.log_security_event(
            session=db,
            event_type="DIRECT_INJECTION",
            threat_level=sec_scan.threat_level,
            source_type="QUERY",
            source_id=query_id,
            detected_pattern=sec_scan.detected_pattern or "Direct prompt injection attempt",
            action_taken="BLOCKED",
        )
        await CryptographicAuditLedger.append_event(
            session=db,
            event_type="SECURITY_THREAT_BLOCKED",
            actor_id="SECURITY_AIRLOCK",
            query_id=query_id,
            payload={"threat": sec_scan.threat_category, "pattern": sec_scan.detected_pattern},
        )
        await db.commit()

        return VerificationResponse(
            query_id=query_id,
            response_id=f"RSP-SEC-{uuid.uuid4().hex[:8]}",
            query_text=req.query,
            response_text=blocked_text,
            trust_profile=sec_profile,
            claims=[],
            evidence_anchors=[],
            is_insufficient_evidence=False,
            contradictions_detected=[],
            total_latency_ms=round(total_latency_ms, 2),
            generated_at=datetime.now(timezone.utc),
        )

    # ── STEP 0.5: Privacy Shield Screening & Pseudonymization ───────────────────
    priv_scan = PrivacyShield.scan_and_pseudonymize(req.query)
    effective_query = priv_scan.protected_text if priv_scan.has_pii else req.query
    if priv_scan.has_pii:
        await PrivacyShield.log_privacy_events(
            session=db,
            source_type="QUERY",
            entities=priv_scan.entities_detected,
        )
        await CryptographicAuditLedger.append_event(
            session=db,
            event_type="PRIVACY_REDACTION",
            actor_id="PRIVACY_SHIELD",
            payload={"entities_masked": priv_scan.total_redactions},
        )

    # ── STEP 1: Pre-Retrieval Risk Classification ──────────────────────────────
    # Run initial risk assessment before any retrieval or generation.
    # TIER 5 (PATIENT_SPECIFIC) is blocked immediately without touching the index.
    pre_risk = QueryRiskEngine.assess(query=req.query, evidence_coverage_pct=100.0)

    if pre_risk.should_block and pre_risk.risk_tier == TIER_PATIENT_SPECIFIC:
        # Hard block: PHI detected, save query record and return blocked response.
        query_id = f"QRY-{uuid.uuid4().hex[:12]}"
        total_latency_ms = (time.perf_counter() - total_start) * 1000.0
        blocked_response_text = (
            "⛔ BLOCKED BY SAFETY POLICY: This query contains potential protected health "
            "information (PHI/PII). For patient-specific clinical decisions, consult "
            "directly with a licensed clinician. No AI response was generated."
        )
        block_profile = TrustProfileRead(
            evidence_coverage_pct=0.0,
            mean_grounding_score=0.0,
            retrieval_quality_score=0.0,
            source_quality_tier="BLOCKED",
            contradiction_risk="LOW",
            privacy_risk="HIGH",
            security_risk="PHI_DETECTED",
            query_risk_tier=pre_risk.risk_tier,
            uncertainty_score=1.0,
            final_status="BLOCKED",
            human_review_required=True,
        )
        query_record = Query(
            id=query_id,
            raw_query_text="[PHI REDACTED]",
            protected_query_text="[PHI REDACTED]",
            query_risk_tier=pre_risk.risk_tier,
            pii_count=len(pre_risk.pii_indicators_found),
            status="BLOCKED",
            total_latency_ms=round(total_latency_ms, 2),
        )
        db.add(query_record)
        await db.flush()
        await ReviewQueueManager.enqueue(
            session=db,
            query_id=query_id,
            response_id=None,
            risk_tier=pre_risk.risk_tier,
            review_reason=pre_risk.review_reason or "PHI detected in query.",
            trust_profile_summary=json.dumps({"final_status": "BLOCKED", "privacy_risk": "HIGH"}),
            is_auto_routed=True,
        )
        await db.commit()
        return VerificationResponse(
            query_id=query_id,
            response_id=f"RSP-BLOCKED-{uuid.uuid4().hex[:8]}",
            query_text="[PHI REDACTED]",
            response_text=blocked_response_text,
            trust_profile=block_profile,
            claims=[],
            evidence_anchors=[],
            is_insufficient_evidence=False,
            contradictions_detected=[],
            total_latency_ms=round(total_latency_ms, 2),
            generated_at=datetime.now(timezone.utc),
        )

    # ── STEP 2: Hybrid Retrieval & Provenance Resolution ──────────────────────
    raw_candidates = retrieval_engine.search(
        query=req.query,
        top_k=req.top_k,
        mode=req.mode,
        alpha=req.alpha,
    )
    evidence_anchors = await ProvenanceResolver.resolve_evidence_items(
        session=db,
        retrieved_raw_items=raw_candidates,
    )

    # ── STEP 3: Grounded LLM Generation ───────────────────────────────────────
    gen_result = await llm_client.generate(
        query=req.query,
        evidence=evidence_anchors,
        preferred_provider=req.model_provider,
    )

    # ── STEP 4: Claim Decomposition & Trust Profile Evaluation ────────────────
    eval_output = trust_engine.evaluate(
        query=req.query,
        response_text=gen_result.response_text,
        evidence_anchors=evidence_anchors,
        query_risk_tier=pre_risk.risk_tier,
    )

    # ── STEP 5: Post-Evidence Risk Override ───────────────────────────────────
    # Apply evidence coverage override (e.g., PERMIT → REVIEW_REQUIRED if low coverage)
    post_risk = QueryRiskEngine.assess(
        query=req.query,
        evidence_coverage_pct=eval_output.trust_profile.evidence_coverage_pct,
    )
    # Use the more restrictive policy between pre and post risk
    effective_policy = post_risk.policy if POLICY_REVIEW_REQUIRED in (
        pre_risk.policy, post_risk.policy
    ) else pre_risk.policy
    effective_human_review = pre_risk.human_review_required or post_risk.human_review_required
    # Update trust profile risk tier to actual assessed tier
    eval_output.trust_profile.query_risk_tier = post_risk.risk_tier
    eval_output.trust_profile.human_review_required = effective_human_review

    # Apply clinical caveat to response if required
    response_text = gen_result.response_text
    if post_risk.clinical_caveat and not eval_output.is_insufficient_evidence:
        response_text = gen_result.response_text + "\n\n" + post_risk.clinical_caveat

    total_latency_ms = (time.perf_counter() - total_start) * 1000.0

    # ── STEP 6: Relational Database Persistence ───────────────────────────────
    query_id = f"QRY-{uuid.uuid4().hex[:12]}"
    response_id = f"RSP-{uuid.uuid4().hex[:12]}"

    query_record = Query(
        id=query_id,
        raw_query_text=req.query,
        protected_query_text=req.query,
        query_risk_tier=post_risk.risk_tier,
        pii_count=len(post_risk.pii_indicators_found),
        status=eval_output.trust_profile.final_status,
        total_latency_ms=round(total_latency_ms, 2),
    )
    db.add(query_record)
    await db.flush()

    # Save Retrieved Evidence Links
    ev_record_map = {}
    for item in evidence_anchors:
        ev_rec = RetrievedEvidence(
            id=str(uuid.uuid4()),
            query_id=query_id,
            chunk_id=item.chunk_id,
            dense_score=item.dense_score,
            sparse_score=item.sparse_score,
            rrf_score=item.rrf_score,
            rerank_score=item.rerank_score,
            rank_position=item.rank_position,
            is_selected=True,
        )
        db.add(ev_rec)
        ev_record_map[item.chunk_id] = ev_rec.id

    await db.flush()

    # Save Generated Response Record
    response_record = GeneratedResponse(
        id=response_id,
        query_id=query_id,
        model_provider=gen_result.model_provider,
        model_name=gen_result.model_name,
        response_text=response_text,
        evidence_coverage_pct=eval_output.trust_profile.evidence_coverage_pct,
        mean_grounding_score=eval_output.trust_profile.mean_grounding_score,
        retrieval_quality_score=eval_output.trust_profile.retrieval_quality_score,
        uncertainty_score=eval_output.trust_profile.uncertainty_score,
        contradiction_risk_score=1.0 if eval_output.trust_profile.contradiction_risk == "HIGH" else 0.0,
        prompt_tokens=gen_result.prompt_tokens,
        completion_tokens=gen_result.completion_tokens,
        generation_latency_ms=gen_result.latency_ms,
        verification_latency_ms=eval_output.verification_latency_ms,
        final_status=eval_output.trust_profile.final_status,
    )
    db.add(response_record)
    await db.flush()

    # Save Claims and Claim-Evidence Links
    for claim_item in eval_output.verified_claims:
        claim_rec = Claim(
            id=f"CLM-{uuid.uuid4().hex[:10]}",
            response_id=response_id,
            claim_index=claim_item.claim_index,
            claim_text=claim_item.claim_text,
            status=claim_item.status,
            grounding_score=claim_item.grounding_score,
            contradiction_score=claim_item.contradiction_score,
            explanation=claim_item.explanation,
        )
        db.add(claim_rec)
        await db.flush()

        for link in claim_item.evidence_links:
            link_rec = ClaimEvidenceLink(
                id=str(uuid.uuid4()),
                claim_id=claim_rec.id,
                evidence_id=ev_record_map.get(link.chunk_id),
                chunk_id=link.chunk_id,
                entailment_score=link.entailment_score,
                citation_page=link.citation_page,
                citation_section=link.citation_section,
            )
            db.add(link_rec)

    # ── STEP 7: Auto-Enqueue to Review Queue if Required ──────────────────────
    if effective_human_review:
        profile_summary = json.dumps({
            "final_status": eval_output.trust_profile.final_status,
            "evidence_coverage_pct": eval_output.trust_profile.evidence_coverage_pct,
            "mean_grounding_score": eval_output.trust_profile.mean_grounding_score,
            "contradiction_risk": eval_output.trust_profile.contradiction_risk,
            "uncertainty_score": eval_output.trust_profile.uncertainty_score,
        })
        await ReviewQueueManager.enqueue(
            session=db,
            query_id=query_id,
            response_id=response_id,
            risk_tier=post_risk.risk_tier,
            review_reason=post_risk.review_reason or f"Risk tier {post_risk.risk_tier} requires human review.",
            trust_profile_summary=profile_summary,
            is_auto_routed=True,
        )

    # ── STEP 8: Cryptographically Chained Rolling Audit Ledger ──────────────
    await CryptographicAuditLedger.append_event(
        session=db,
        event_type="QUERY_VERIFIED",
        actor_id="VERIFICATION_ENGINE",
        query_id=query_id,
        payload={
            "status": eval_output.trust_profile.final_status,
            "coverage": eval_output.trust_profile.evidence_coverage_pct,
            "grounding": eval_output.trust_profile.mean_grounding_score,
            "risk_tier": post_risk.risk_tier,
            "claims_count": len(eval_output.verified_claims),
        },
    )

    await db.commit()

    return VerificationResponse(
        query_id=query_id,
        response_id=response_id,
        query_text=req.query,
        response_text=response_text,
        trust_profile=eval_output.trust_profile,
        claims=eval_output.verified_claims,
        evidence_anchors=evidence_anchors,
        is_insufficient_evidence=eval_output.is_insufficient_evidence,
        contradictions_detected=eval_output.detected_conflicts,
        total_latency_ms=round(total_latency_ms, 2),
        generated_at=datetime.now(timezone.utc),
    )


@router.post(
    "/verify-text",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify user-provided arbitrary clinical text against indexed evidence anchors",
)
async def verify_arbitrary_text(
    req: VerifyTextRequest,
    db: AsyncSession = Depends(get_db),
):
    total_start = time.perf_counter()

    query_str = req.query_context or req.text_to_verify[:150]
    raw_candidates = retrieval_engine.search(query=query_str, top_k=req.top_k)
    evidence_anchors = await ProvenanceResolver.resolve_evidence_items(
        session=db,
        retrieved_raw_items=raw_candidates,
    )

    eval_output = trust_engine.evaluate(
        query=query_str,
        response_text=req.text_to_verify,
        evidence_anchors=evidence_anchors,
    )
    total_latency = (time.perf_counter() - total_start) * 1000.0

    return VerificationResponse(
        query_id=f"QRY-TEXT-{uuid.uuid4().hex[:8]}",
        response_id=f"RSP-TEXT-{uuid.uuid4().hex[:8]}",
        query_text=query_str,
        response_text=req.text_to_verify,
        trust_profile=eval_output.trust_profile,
        claims=eval_output.verified_claims,
        evidence_anchors=evidence_anchors,
        is_insufficient_evidence=eval_output.is_insufficient_evidence,
        contradictions_detected=eval_output.detected_conflicts,
        total_latency_ms=round(total_latency, 2),
        generated_at=datetime.now(timezone.utc),
    )


@router.get(
    "/{response_id}",
    response_model=VerificationResponse,
    summary="Retrieve full claim verification profile and evidence links by response ID",
)
async def get_verification_details(
    response_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(GeneratedResponse)
        .where(GeneratedResponse.id == response_id)
        .options(
            selectinload(GeneratedResponse.query),
            selectinload(GeneratedResponse.claims)
            .selectinload(Claim.evidence_links)
            .selectinload(ClaimEvidenceLink.chunk)
            .selectinload(DocumentChunk.document),
            selectinload(GeneratedResponse.claims)
            .selectinload(Claim.evidence_links)
            .selectinload(ClaimEvidenceLink.chunk)
            .selectinload(DocumentChunk.version),
        )
    )
    res = await db.execute(stmt)
    resp_obj = res.scalar_one_or_none()
    if not resp_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification response with ID '{response_id}' not found.",
        )

    claims_list: list[ClaimRead] = []
    for c in resp_obj.claims:
        links: list[ClaimEvidenceLinkRead] = []
        for l in c.evidence_links:
            doc_title = l.chunk.document.title if (l.chunk and l.chunk.document) else None
            doc_ver = l.chunk.version.version_tag if (l.chunk and l.chunk.version) else None
            links.append(
                ClaimEvidenceLinkRead(
                    id=l.id,
                    chunk_id=l.chunk_id,
                    entailment_score=l.entailment_score,
                    citation_page=l.citation_page,
                    citation_section=l.citation_section,
                    document_title=doc_title,
                    document_version=doc_ver,
                )
            )
        claims_list.append(
            ClaimRead(
                id=c.id,
                claim_index=c.claim_index,
                claim_text=c.claim_text,
                status=c.status,
                grounding_score=c.grounding_score,
                contradiction_score=c.contradiction_score,
                explanation=c.explanation,
                evidence_links=links,
            )
        )

    profile = TrustProfileRead(
        evidence_coverage_pct=resp_obj.evidence_coverage_pct,
        mean_grounding_score=resp_obj.mean_grounding_score,
        retrieval_quality_score=resp_obj.retrieval_quality_score,
        source_quality_tier="HIGH (Peer-reviewed Guideline)",
        contradiction_risk="HIGH" if resp_obj.contradiction_risk_score > 0 else "LOW",
        privacy_risk="LOW",
        security_risk="CLEAR",
        query_risk_tier=resp_obj.query.query_risk_tier if resp_obj.query else "CLINICAL_RECOMMENDATION",
        uncertainty_score=resp_obj.uncertainty_score,
        final_status=resp_obj.final_status,
        human_review_required=(resp_obj.final_status != "VERIFIED"),
    )

    return VerificationResponse(
        query_id=resp_obj.query_id,
        response_id=resp_obj.id,
        query_text=resp_obj.query.raw_query_text if resp_obj.query else "",
        response_text=resp_obj.response_text,
        trust_profile=profile,
        claims=claims_list,
        evidence_anchors=[],
        is_insufficient_evidence=(resp_obj.final_status == "INSUFFICIENT_EVIDENCE"),
        contradictions_detected=[],
        total_latency_ms=round(resp_obj.generation_latency_ms + resp_obj.verification_latency_ms, 2),
        generated_at=resp_obj.created_at,
    )
