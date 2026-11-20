import time
from dataclasses import dataclass
from backend.app.schemas.retrieval import RetrievedEvidenceItem
from backend.app.schemas.verification import ClaimRead, TrustProfileRead
from backend.app.services.verification.claim_extractor import ClaimExtractor
from backend.app.services.verification.contradiction import ContradictionDetector
from backend.app.services.verification.nli_matcher import NLIMatcher


@dataclass
class TrustEvaluationOutput:
    trust_profile: TrustProfileRead
    verified_claims: list[ClaimRead]
    detected_conflicts: list[str]
    is_insufficient_evidence: bool
    verification_latency_ms: float


class TrustEngine:
    """Orchestrates atomic claim decomposition, NLI grounding verification, and Trust Profile derivation."""

    @classmethod
    def evaluate(
        cls,
        query: str,
        response_text: str,
        evidence_anchors: list[RetrievedEvidenceItem],
        query_risk_tier: str = "CLINICAL_RECOMMENDATION",
    ) -> TrustEvaluationOutput:
        start_time = time.perf_counter()

        # 1. Check for Empty Evidence Yield
        if not evidence_anchors:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            profile = TrustProfileRead(
                evidence_coverage_pct=0.0,
                mean_grounding_score=0.0,
                retrieval_quality_score=0.0,
                source_quality_tier="NONE (No Evidence Anchors)",
                contradiction_risk="LOW",
                privacy_risk="LOW",
                security_risk="CLEAR",
                query_risk_tier=query_risk_tier,
                uncertainty_score=1.0,
                final_status="INSUFFICIENT_EVIDENCE",
                human_review_required=True,
            )
            return TrustEvaluationOutput(
                trust_profile=profile,
                verified_claims=[],
                detected_conflicts=[],
                is_insufficient_evidence=True,
                verification_latency_ms=round(latency_ms, 2),
            )

        # 2. Atomic Claim Decomposition
        raw_claims = ClaimExtractor.extract_claims(response_text)
        if not raw_claims:
            raw_claims = [response_text.strip()]

        # 3. NLI Claim-to-Evidence Grounding Verification
        verified_claims: list[ClaimRead] = []
        n_supported = 0
        n_partial = 0
        total_grounding = 0.0

        for idx, claim_str in enumerate(raw_claims, start=1):
            res = NLIMatcher.verify_claim(idx, claim_str, evidence_anchors)
            total_grounding += res.grounding_score

            if res.status == "SUPPORTED":
                n_supported += 1
            elif res.status == "PARTIALLY_SUPPORTED":
                n_partial += 1

            links = [res.best_evidence_link] if res.best_evidence_link else []

            verified_claims.append(
                ClaimRead(
                    id=f"CLM-{idx:03d}",
                    claim_index=idx,
                    claim_text=claim_str,
                    status=res.status,
                    grounding_score=res.grounding_score,
                    contradiction_score=res.contradiction_score,
                    explanation=res.explanation,
                    evidence_links=links,
                )
            )

        n_total = len(verified_claims)
        evidence_coverage_pct = round(((n_supported + 0.5 * n_partial) / n_total) * 100.0, 2)
        mean_grounding = round(total_grounding / n_total, 4)

        # 4. Contradiction & Inter-Guideline Discrepancy Detection
        contra_res = ContradictionDetector.analyze_evidence_set(evidence_anchors, response_text, query=query)

        # 5. Retrieval Quality Score
        retrieval_quality = 0.0
        if evidence_anchors:
            retrieval_quality = sum(e.rerank_score for e in evidence_anchors) / len(evidence_anchors)
        retrieval_quality = round(min(1.0, max(0.0, retrieval_quality)), 4)

        # 6. Uncertainty Rating Calculation
        # U = 1.0 - (0.4 * (Cov/100) + 0.3 * Q_ret + 0.3 * Q_src) + 0.4 * R_contra
        cov_norm = evidence_coverage_pct / 100.0
        uncertainty = 1.0 - (0.45 * cov_norm + 0.35 * retrieval_quality + 0.20 * 0.90) + (0.35 * contra_res.contradiction_risk_score)
        uncertainty_score = round(min(1.0, max(0.0, uncertainty)), 4)

        # 7. Final Status Determination
        if response_text.startswith("INSUFFICIENT EVIDENCE") or evidence_coverage_pct < 60.0:
            final_status = "INSUFFICIENT_EVIDENCE"
            review_req = True
        elif contra_res.has_contradiction:
            final_status = "CONTRADICTORY"
            review_req = True
        elif evidence_coverage_pct >= 85.0:
            final_status = "VERIFIED"
            review_req = False
        else:
            final_status = "PARTIALLY_VERIFIED"
            review_req = True

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        profile = TrustProfileRead(
            evidence_coverage_pct=evidence_coverage_pct,
            mean_grounding_score=mean_grounding,
            retrieval_quality_score=retrieval_quality,
            source_quality_tier="HIGH (Peer-reviewed Guideline)" if evidence_anchors[0].provenance.tier == 1 else "TIER 2 (Institutional SOP)",
            contradiction_risk="HIGH" if contra_res.has_contradiction else "LOW",
            privacy_risk="LOW",
            security_risk="CLEAR",
            query_risk_tier=query_risk_tier,
            uncertainty_score=uncertainty_score,
            final_status=final_status,
            human_review_required=review_req,
        )

        return TrustEvaluationOutput(
            trust_profile=profile,
            verified_claims=verified_claims,
            detected_conflicts=contra_res.detected_conflicts,
            is_insufficient_evidence=(final_status == "INSUFFICIENT_EVIDENCE"),
            verification_latency_ms=round(latency_ms, 2),
        )


# Global singleton instance
trust_engine = TrustEngine()
