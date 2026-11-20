# MEDTRUST-ENGINE: Trust Model & Verification Methodology
**Document ID:** TRUST-MEDTRUST-2026-V1.0  
**Status:** Approved for Implementation  
**Classification:** Trustworthy AI Verification Framework  
**Core Principle:** EVIDENCE BEFORE CONFIDENCE

---

## 1. Trust Philosophy & Faculty Pedagogical Model

### 1.1 The "Open-Book Student + Strict Examiner" Analogy
```
+---------------------------------------------------------------------------------------+
|                       FACULTY EXPLANATION MODEL: EXAM METAPHOR                        |
+---------------------------+-----------------------------------+-----------------------+
| Component                 | Academic Analogy                  | MedTrust Role         |
+---------------------------+-----------------------------------+-----------------------+
| Clinical Guidelines       | The Authoritative Textbook        | Ground-truth corpus   |
| Generative LLM            | The Student taking the Exam       | Synthesis & draft text|
| Claim Decomposer          | Breaking answer into statements   | Atomic propositioning |
| Claim Verifier / NLI      | The Strict Examiner               | Verifying citations   |
| Insufficient Evidence     | Student admitting "Not in book"   | Epistemic honesty     |
| Review Queue              | Escalation to Department Chair    | Human oversight       |
+---------------------------+-----------------------------------+-----------------------+
```

### 1.2 The Zero-G Epistemic Drift Analogy
```
"In unconstrained LLMs, generated knowledge has no intrinsic gravity.
It floats freely and is easily perturbed into hallucination.
MedTrust creates Evidence Anchors (verified document chunks).
Claims that remain tightly tethered to these anchors have High Gravity.
Claims that drift away into ungrounded speculation lose gravity,
triggering the Trust Engine to arrest their flight and demand human review."
```

---

## 2. Multi-Dimensional Trust Profile

MedTrust rejects single opaque "confidence scores". Instead, it computes a deterministic, multi-dimensional **Trust Profile**:

```text
MEDTRUST TRUST PROFILE
--------------------------------------------------
Evidence Coverage:       92.5%  [==================  ]
Claim Grounding:         89.0%  [=================   ]
Retrieval Quality:       94.2%  [=================== ]
Source Quality:          HIGH (Peer-reviewed Guideline 2026)
Contradiction Risk:      NONE (0 conflicts detected)
Privacy Risk:            LOW (3 PII entities protected)
Security Risk:           CLEAR (Airlock Screened)
Query Risk Tier:         CLINICAL_RECOMMENDATION (Tier 3)
Uncertainty Rating:      LOW (8.5%)
--------------------------------------------------
FINAL DECISION STATUS:   VERIFIED / LOW RESIDUAL RISK
HUMAN OVERSIGHT:         OPTIONAL AUDIT
```

---

## 3. Mathematical Definitions & Derivations

### 3.1 Retrieval Quality Metric ($Q_{ret}$)
$$Q_{ret} = \frac{1}{K} \sum_{j=1}^K \left[ w_{dense} \cdot S_{dense}(E_j) + w_{sparse} \cdot \tilde{S}_{bm25}(E_j) \right] \times R_{rerank}(E_j)$$

### 3.2 Claim-Level Grounding Score ($G(C_i)$)
$$G(C_i) = \max_{j \in \{1, \dots, K\}} \text{EntailmentScore}(C_i, E_j)$$
- **SUPPORTED:** $G(C_i) \ge 0.80$
- **PARTIALLY_SUPPORTED:** $0.50 \le G(C_i) < 0.80$
- **UNSUPPORTED:** $G(C_i) < 0.50$
- **CONTRADICTED:** $\text{ContradictionScore}(C_i, E_j) \ge 0.70$

### 3.3 Evidence Coverage ($Cov_{ev}$)
$$Cov_{ev} = \frac{N_{supp} + 0.5 \cdot N_{part}}{N_{total}} \times 100\%$$

---

## 4. Status Taxonomy

- `VERIFIED`: High evidence coverage ($\ge 85\%$) and zero contradictions.
- `PARTIALLY_VERIFIED`: Moderate coverage ($65\% \le Cov < 85\%$) with flagged ungrounded claims.
- `INSUFFICIENT_EVIDENCE`: Coverage $< 65\%$ or retrieval score $< 0.40$; definitive answer restricted.
- `CONTRADICTORY`: Multiple sources disagree; routed to review queue.
- `REVIEW_REQUIRED`: High-risk query or unsupported clinical dosage claim.
- `BLOCKED`: Security Airlock threat detected.
- `ERROR`: Subsystem exception handled gracefully.
