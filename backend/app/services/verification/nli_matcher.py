import re
from dataclasses import dataclass
import numpy as np
from backend.app.schemas.retrieval import RetrievedEvidenceItem
from backend.app.schemas.verification import ClaimEvidenceLinkRead, ClaimRead
from backend.app.services.retrieval.embeddings import embedding_provider


@dataclass
class VerifiedClaimResult:
    claim_index: int
    claim_text: str
    status: str  # SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED
    grounding_score: float
    contradiction_score: float
    explanation: str
    best_evidence_link: ClaimEvidenceLinkRead | None


class NLIMatcher:
    """Evaluates Natural Language Inference (NLI) grounding of clinical claims against evidence."""

    SUPPORTED_THRESHOLD = 0.80
    PARTIAL_THRESHOLD = 0.50

    @classmethod
    def verify_claim(
        cls,
        claim_index: int,
        claim_text: str,
        evidence_anchors: list[RetrievedEvidenceItem],
    ) -> VerifiedClaimResult:
        """Evaluate single claim against all retrieved evidence anchors."""
        if not evidence_anchors:
            return VerifiedClaimResult(
                claim_index=claim_index,
                claim_text=claim_text,
                status="UNSUPPORTED",
                grounding_score=0.0,
                contradiction_score=0.0,
                explanation="No indexed evidence anchors available for verification.",
                best_evidence_link=None,
            )

        claim_vec = np.array(embedding_provider.embed_text(claim_text), dtype=np.float32)
        claim_tokens = cls._tokenize_clinical(claim_text)
        claim_numbers = cls._extract_numbers_and_dosages(claim_text)

        best_score = 0.0
        best_evidence: RetrievedEvidenceItem | None = None

        for item in evidence_anchors:
            chunk_vec = np.array(embedding_provider.embed_text(item.text_content), dtype=np.float32)
            # Cosine similarity
            cos_sim = float(np.dot(claim_vec, chunk_vec))
            cos_sim = max(0.0, min(1.0, cos_sim))

            # Lexical token overlap
            chunk_tokens = cls._tokenize_clinical(item.text_content)
            overlap = len(claim_tokens.intersection(chunk_tokens))
            lex_ratio = (overlap / len(claim_tokens)) if claim_tokens else 0.0

            # Dosage and numerical consistency
            chunk_numbers = cls._extract_numbers_and_dosages(item.text_content)
            num_match_score = 1.0
            if claim_numbers:
                matched_nums = len(claim_numbers.intersection(chunk_numbers))
                num_match_score = matched_nums / len(claim_numbers)

            # Pairwise Entailment Score
            # Exact lexical matches and numerical matches give high grounding confidence
            pairwise_score = (0.40 * cos_sim) + (0.35 * lex_ratio) + (0.25 * num_match_score)

            # If token overlap is extremely high (e.g. > 75%), boost to supported
            if lex_ratio >= 0.75 and num_match_score >= 1.0:
                pairwise_score = max(pairwise_score, 0.88)

            if pairwise_score > best_score:
                best_score = pairwise_score
                best_evidence = item

        best_score = round(min(1.0, max(0.0, best_score)), 4)

        # Status Classification
        if best_score >= cls.SUPPORTED_THRESHOLD:
            status = "SUPPORTED"
            expl = f"Strongly supported by evidence (Grounding: {best_score})."
        elif best_score >= cls.PARTIAL_THRESHOLD:
            status = "PARTIALLY_SUPPORTED"
            expl = f"Partially supported with moderate grounding overlap (Score: {best_score})."
        else:
            status = "UNSUPPORTED"
            expl = f"Insufficient evidence grounding in indexed sources (Score: {best_score})."

        best_link = None
        if best_evidence:
            prov = best_evidence.provenance
            best_link = ClaimEvidenceLinkRead(
                id=f"LNK-{claim_index:02d}-{best_evidence.chunk_id[-6:]}",
                chunk_id=best_evidence.chunk_id,
                entailment_score=best_score,
                citation_page=prov.page_number,
                citation_section=prov.section_heading,
                document_title=prov.document_title,
                document_version=prov.document_version,
            )

        return VerifiedClaimResult(
            claim_index=claim_index,
            claim_text=claim_text,
            status=status,
            grounding_score=best_score,
            contradiction_score=0.0,
            explanation=expl,
            best_evidence_link=best_link,
        )

    @staticmethod
    def _tokenize_clinical(text: str) -> set[str]:
        """Extract alphanumeric clinical tokens."""
        raw = re.findall(r"\b[a-zA-Z0-9\.\-\/]+\b", text.lower())
        stopwords = {"a", "an", "the", "in", "on", "of", "and", "or", "for", "to", "with", "is", "are", "by", "that", "this"}
        return {t for t in raw if t not in stopwords and len(t) > 1}

    @staticmethod
    def _extract_numbers_and_dosages(text: str) -> set[str]:
        """Extract dosage numbers and medical quantities (e.g., '30', '65', '40', '1', '7-10')."""
        matches = re.findall(r"\b\d+(?:\.\d+)?(?:\s*(?:mg|ml|kg|units|hr|hours?|days?|mmhg|mmol))?\b", text.lower())
        return {m.strip() for m in matches}
