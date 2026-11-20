# MEDTRUST-ENGINE: Requirements Analysis & Specification
**Document ID:** REQ-MEDTRUST-2026-V1.0  
**Status:** Approved for Architecture Design  
**Classification:** Clinical Decision-Support & Trustworthy AI Verification Platform  
**Metaphor Layer:** Zero-G / Anti-Gravity Clinical Evidence Framework

---

## 1. Executive Summary & Problem Statement

### 1.1 Clinical Context
Generative Artificial Intelligence (GenAI) and Large Language Models (LLMs) have demonstrated immense capability in clinical summarization, protocol synthesis, and literature search. However, standard LLMs operate probabilistically without inherent epistemic grounding:
- **Hallucination Risk:** Generating fluent, plausible, but clinically false recommendations.
- **Parametric Drift:** Relying on unverified training data rather than authorized, versioned institutional guidelines.
- **Vulnerability to Injection:** Susceptible to direct and indirect prompt injections embedded within untrusted clinical PDFs.
- **Privacy Breaches:** Leaking Protected Health Information (PHI/PII) into model prompts and downstream audit logs.
- **Lack of Claim Traceability:** Presenting monolithic responses without fine-grained claim-to-evidence provenance.
- **Silent Failures under Uncertainty:** Fabricating answers when retrieved context is insufficient or conflicting.

### 1.2 The MedTrust Mission
**MedTrust-Engine** is a modular, privacy-preserving, security-screened, evidence-anchored clinical AI verification and decision-support platform. The platform enforces the foundational principle:

> **EVIDENCE BEFORE CONFIDENCE**  
> *"Knowledge has no gravity by itself. Evidence Anchors give clinical facts a trustworthy reference point. When claims drift from their evidence anchors, the Trust Engine flags the anomaly, measures uncertainty, and routes the case to human oversight."*

---

## 2. Regulatory & Medical Safety Boundaries

### 2.1 Medical Disclaimer & Scope
- **Non-Diagnostic Scope:** MedTrust is a clinical decision-support and research verification system. It does **not** diagnose conditions, prescribe therapeutic regimens, replace clinician judgment, or make autonomous medical decisions.
- **Truthful Claims Policy:** The system explicitly refrains from claiming "Zero Hallucination," "100% Guaranteed Accuracy," or "HIPAA/GDPR Certified" without legal attestation.
- **Governance Terminology:** Terminology strictly aligns with NIST AI RMF 1.0 (Govern, Map, Measure, Manage) and EU AI Act Risk Management Frameworks (High-Risk AI System Human Oversight, Transparency, and Record-Keeping controls).

---

## 3. User Personas & User Journeys

### 3.1 Personas
1. **Dr. Marcus Vance (Attending Physician / Clinical User):** Needs rapid synthesis of complex, multi-source clinical guidelines (e.g., Sepsis Bundles, Anticoagulation Protocols) with line-item verification and source page citations.
2. **Elena Rostova (Clinical AI Safety & Governance Officer):** Reviews system telemetry, monitors evidence coverage trends, audits privacy redactions, inspects prompt-injection telemetry, and exports NIST-aligned audit trails.
3. **Dr. Sarah Chen (Senior Peer Reviewer / Human-in-the-Loop):** Operates the Review Queue, adjudicating borderline claims, resolving guideline version conflicts, and marking unsupported statements.
4. **Devon Miller (Clinical Informatics & QA Engineer):** Executes evaluation benchmarks, checks hybrid retrieval accuracy, assesses PII detection sensitivity, and monitors latency/token overhead.

### 3.2 Key User Journeys
- **Journey 1 (Grounded Inquiry):** Clinician submits query $\to$ Security Airlock scans $\to$ Privacy Shield redacts $\to$ Hybrid Retrieval fetches candidate chunks $\to$ Reranker selects top evidence $\to$ LLM generates grounded draft $\to$ Claim Verifier validates every atomic assertion $\to$ Full Trust Profile and Evidence Anchors presented.
- **Journey 2 (Uncertainty Refusal):** Clinician queries unindexed topic $\to$ Retrieval yield low $\to$ Insufficient Evidence detector blocks definitive generation $\to$ Informational warning returned with recommendation for human consult.
- **Journey 3 (Malicious PDF Quarantine):** Ingestion receives PDF with hidden white-text prompt injection $\to$ Security Airlock detects delimiter breakout patterns $\to$ Document quarantined, security event logged, injection isolated from LLM instruction channel.
- **Journey 4 (Contradiction Adjudication):** Query spans 2024 vs 2026 guidelines $\to$ System detects conflicting dosage recommendations $\to$ Flags "Potential Source Conflict" $\to$ Routes to Review Queue for clinician review.

---

## 4. Functional Requirements (FR)

### FR-1: Document Ingestion & Integrity
- **FR-1.1:** Ingest PDF, TXT, and Markdown clinical guidelines with format validation and MIME-type verification.
- **FR-1.2:** Compute cryptographic content hashes (SHA-256) per document and per chunk for tamper-evident provenance.
- **FR-1.3:** Extract structured metadata: Document ID, Title, Clinical Domain, Publication Date, Version, Authoring Body, and Status (Active, Superseded, Quarantined).
- **FR-1.4:** Support document version comparison and explicit marking of superseded documents.

### FR-2: Security Airlock (Adversarial Defense)
- **FR-2.1:** Detect direct prompt injection in queries (jailbreak heuristics, system prompt exfiltration patterns, roleplay overrides).
- **FR-2.2:** Detect indirect prompt injection inside ingested documents (delimiter manipulation, instruction tags in raw text, adversarial suffixes).
- **FR-2.3:** Enforce strict architectural separation between System Instructions and Untrusted Document Data.
- **FR-2.4:** Generate Security Events with threat classification, severity rating, and containment action.

### FR-3: Privacy Shield (PII / PHI Redaction)
- **FR-3.1:** Detect 18 HIPAA Safe Harbor identifier classes (Names, MRNs, Phone Numbers, Emails, SSNs, Dates, Geographic Data).
- **FR-3.2:** Execute dual-tier detection: Deterministic Regex + Contextual Medical Named Entity Recognition (NER).
- **FR-3.3:** Apply reversible pseudonymization tokenization (`[PATIENT_ID_001]`, `[DATE_001]`) for internal processing while preventing PII leakage into external LLM prompts and audit storage.
- **FR-3.4:** Provide side-by-side Raw vs. Protected inspection view with redaction statistics.

### FR-4: Semantic Chunking & Provenance
- **FR-4.1:** Chunk clinical text preserving structural boundaries (sections, numbered lists, clinical recommendations, tables).
- **FR-4.2:** Maintain chunk provenance: `Document ID`, `Page Number`, `Section Heading`, `Paragraph/Block Index`, `Chunk ID`, `Content Hash`.
- **FR-4.3:** Overlap chunks intelligently (15-20% window) to prevent clinical context truncation.

### FR-5: Hybrid Retrieval & Reranking
- **FR-5.1:** Dense Semantic Retrieval using dense embedding models (FAISS vector store).
- **FR-5.2:** Sparse Keyword Retrieval using BM25Okapi for precise clinical terminology, acronyms, and drug dosages.
- **FR-5.3:** Reciprocal Rank Fusion (RRF) with configurable density/sparsity weighting.
- **FR-5.4:** Cross-Encoder / High-precision Reranking to reorder top-N candidates into top-K evidence anchors.

### FR-6: Grounded Generation & Claim-Level Verification
- **FR-6.1:** Generate answers constrained strictly to provided evidence chunks.
- **FR-6.2:** Atomic Claim Decomposition: Parse LLM answer into discrete, verifiable factual claims.
- **FR-6.3:** Claim NLI / Grounding Verification: Classify each claim as `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, or `CONTRADICTED`.
- **FR-6.4:** Map each verified claim to exact Evidence Anchors (Document, Page, Section, Chunk ID, Similarity Score).
- **FR-6.5:** Calculate interpretable **Evidence Coverage %** ($\frac{\text{Supported Claims}}{\text{Total Claims}} \times 100$).

### FR-7: Risk Engine & Insufficient Evidence Handling
- **FR-7.1:** Query Risk Classification: Categorize queries into Informational (Low), Interpretive (Moderate), Clinical Recommendation (Higher), Dosage/Treatment (High), and Patient-Specific (Very High).
- **FR-7.2:** Enforce dynamic safety policies: Stricter evidence thresholds and mandatory human review as query risk elevates.
- **FR-7.3:** Refusal Policy: If Evidence Coverage < Threshold (e.g., 60%) or top retrieval score < cutoff, trigger `INSUFFICIENT EVIDENCE` response state and restrict unverified generation.
- **FR-7.4:** Contradiction Detection: Flag conflicting claims across distinct document versions or distinct clinical sources.

### FR-8: Human-in-the-Loop Review Queue
- **FR-8.1:** Automatically enqueue responses flagged with `REVIEW_REQUIRED`, `CONTRADICTION`, `HIGH_RISK`, or `UNSUPPORTED_CLAIMS`.
- **FR-8.2:** Provide reviewer adjudication actions: `Approve`, `Reject`, `Request Re-evaluation`, `Mark Evidence Insufficient`, `Escalate`.
- **FR-8.3:** Track reviewer identity, timestamp, decision rationale, and version diffs.

### FR-9: Governance, Auditing & Tamper-Evident Ledger
- **FR-9.1:** Record comprehensive audit events for every system interaction (Query, Security, Privacy, Verification, Review).
- **FR-9.2:** Implement SHA-256 rolling hash chain across audit log entries to ensure tamper evidence.
- **FR-9.3:** Provide telemetry dashboard with real-time aggregates: Evidence Coverage, Grounding Rate, Review Rate, Security Blocks.
- **FR-9.4:** Export audit trails in CSV and JSON formats.

### FR-10: Automated Evaluation Lab
- **FR-10.1:** Execute 10+ standard benchmark cases (Supported, Unsupported, Injections, PII, High-risk dosage, Version conflict, etc.).
- **FR-10.2:** Compute empirical metrics: Retrieval Precision@K, Claim Verification Accuracy, Injection Detection Rate, PII Recall, Refusal Rate, Latency.
- **FR-10.3:** Store evaluation runs with timestamped diffs for regression testing.

---

## 5. Non-Functional Requirements (NFR)

| ID | Category | Specification |
|:---|:---|:---|
| **NFR-1** | **Performance** | End-to-end query verification latency < 3.5s for cached/local models; retrieval latency < 150ms. |
| **NFR-2** | **Availability & Fail-Safe** | Graceful degradation if LLM/Vector DB fails; return clear, non-crash error state stating no unverified answer was generated. |
| **NFR-3** | **Security** | Zero API keys or secrets in frontend bundle; strict input validation via Zod & Pydantic; CORS lockdown. |
| **NFR-4** | **Privacy** | Data minimization; zero plaintext PII written to persistent audit logs or external LLM payloads. |
| **NFR-5** | **Explainability** | Visual "Trust Trajectory" rendering every pipeline milestone with deterministic metrics. |
| **NFR-6** | **Usability & Aesthetics** | Professional clinical enterprise interface (no gaming/cartoon graphics); dark/light mode; WCAG 2.1 AA accessible contrast. |
| **NFR-7** | **Modularity** | Decoupled interfaces for LLMProvider, VectorRetriever, SparseRetriever, ClaimExtractor, and RiskEngine. |

---

## 6. Out of Scope (Explicit Non-Goals)
- Autonomous clinical diagnosis or treatment prescribing.
- Direct Electronic Health Record (EHR/HL7 FHIR) production bi-directional write access.
- Distributed Kubernetes clustering / multi-region cloud deployment (prioritizing high-cohesion modular architecture).
