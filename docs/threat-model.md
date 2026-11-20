# MEDTRUST-ENGINE: Threat Model & Security Risk Analysis
**Document ID:** SEC-MEDTRUST-2026-V1.0  
**Status:** Approved for Implementation  
**Classification:** Security Architecture & Adversarial Defense  
**Framework Alignment:** OWASP Top 10 for LLMs (2025/2026) | NIST AI RMF 1.0 | STRIDE

---

## 1. Executive Summary & Security Philosophy

Clinical AI platforms process high-consequence medical guidance and sensitive patient health data. Conventional web application security is necessary but insufficient. MedTrust-Engine implements an **Adversarial Clinical Defense Architecture** that treats all user prompts and ingested documents as untrusted input data.

The Security Airlock enforces a zero-trust boundary around the LLM, vector indexing, and claim verification subsystems.

---

## 2. Threat Actor Profiles

1. **Malicious External Ingester:** Attempts to poison the institutional knowledge base by uploading PDF guidelines laced with indirect prompt injections (e.g., hidden white-text instructions to alter drug dosages).
2. **Adversarial Query Submitter:** Submits direct jailbreak strings (`ignore system instructions`, `simulate unrestricted physician persona`) to exfiltrate system prompts or bypass safety boundaries.
3. **Negligent Internal Clinician:** Pastes unredacted patient notes containing MRNs, names, and contact details into the clinical search box.
4. **Knowledge Drift / Stale Protocol Collisions:** Unintentional administrative conflict where older guidelines (2024) recommend therapies superseded by updated guidelines (2026).
5. **Malicious Insider / Log Tamperer:** Attempts to alter historical audit logs to conceal medical errors or unauthorized queries.

---

## 3. Comprehensive Threat Matrix

```
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                MEDTRUST THREAT ASSESSMENT MATRIX                                              |
+-----+-------------------------------+----------+------------+--------------------------------+--------------------------------+
| ID  | Threat Name                   | Category | Likelihood | Impact                         | Core Mitigation                |
+-----+-------------------------------+----------+------------+--------------------------------+--------------------------------+
| T-01| Direct Prompt Injection       | Tampering| High       | System prompt exfiltration,    | Security Airlock Query Screen, |
|     | (Jailbreaks, Roleplay)        |          |            | safety boundary bypass         | strict role-based separation   |
| T-02| Indirect Prompt Injection     | Tampering| Moderate   | Hijacked generation, altered   | Document scanner, markdown     |
|     | (Hidden PDF instructions)     |          |            | clinical recommendations       | sanitization, data isolation   |
| T-03| PII / PHI Leakage             | Info Disc| High       | HIPAA/GDPR privacy violation,  | Privacy Shield dual-tier NER   |
|     | (Names, MRNs, Contacts)       |          |            | identity disclosure            | & deterministic tokenization   |
| T-04| Epistemic Drift /             | Integrity| High       | Fabricated treatment protocol, | Atomic Claim Decomposition,    |
|     | Clinical Hallucination        |          |            | incorrect medication dosage    | NLI Grounding Verification     |
| T-05| Retrieval Failure /           | DoS /    | Moderate   | Missing critical evidence,     | Hybrid Fusion (Dense + BM25),  |
|     | Vocabulary Mismatch           | Accuracy |            | biased search yield            | Insufficient Evidence Refusal  |
| T-06| Version Collision & Stale     | Integrity| Moderate   | Obsolete clinical protocol     | Document Versioning Engine,    |
|     | Knowledge Drift               |          |            | applied to active care         | Superseded Flagging & Conflict |
| T-07| Conflicting Source Directives | Integrity| Moderate   | Incompatible recommendations   | Cross-Source Contradiction     |
|     | (Guideline A vs B)            |          |            | presented as unified truth     | Detector & Review Escalation   |
| T-08| Denial of Service via Large/  | DoS      | Moderate   | Memory exhaustion, PDF parsing | Stream parsing limits, page cap|
|     | Malformed PDFs                |          |            | buffer overflows               | (max 100), MIME validation     |
| T-09| Audit Log Tampering &         | Repudiat.| Low        | Inability to trace medical     | Cryptographic SHA-256 rolling  |
|     | Post-hoc Alteration           |          |            | decisions or verify lineage    | hash chain ledger              |
| T-10| LLM API Outage /              | Avail.   | Moderate   | Complete service outage or     | Deterministic Extractive       |
|     | Silent Degradation            |          |            | unhandled exception in UI      | Offline Fallback Engine        |
+-----+-------------------------------+----------+------------+--------------------------------+--------------------------------+
```

---

## 4. Deep-Dive Threat Analysis & Mitigation Specifications

### T-01: Direct Prompt Injection & Jailbreaking
- **Airlock Query Filter:** Regex & heuristic pattern matcher scanning for 30+ injection signatures (`ignore previous`, `system override`, `dan mode`, `developer prompt`).
- **Instruction-Data Decoupling:** System instructions are locked in the `system` prompt role. User query is enclosed within strict semantic constraints.
- **Immediate Containment:** Request is aborted prior to LLM dispatch; security event logged with severity `HIGH`.

### T-02: Indirect Prompt Injection via Clinical Documents
- **Document Parsing Sanitizer:** PyMuPDF strips executable scripts, forms, and hidden annotations.
- **Delimiter Isolation:** Evidence chunks are injected into LLM prompts inside structured, immutable boundary tags (`<untrusted_clinical_evidence chunk_id="CH-004">...</untrusted_clinical_evidence>`).
- **Indirect Injection Scanner:** Chunks containing imperative commands directed at AI personas are flagged during ingestion and quarantined.

### T-03: PII / PHI Leakage in Queries and Documents
- **Privacy Shield:** Runs deterministic regex for MRNs, SSNs, phone numbers, emails, and dates, combined with clinical NER for patient/doctor names.
- **Pseudonymization:** Replaces identified entities with tokenized placeholders (`[PATIENT_NAME_001]`, `[MEDICAL_ID_001]`, `[DATE_001]`).
- **Data Minimization:** Raw PII is never stored in persistent audit tables or forwarded to external third-party LLMs.

### T-04: Clinical Hallucination & Epistemic Drift
- **Atomic Claim Decomposition:** The generated response is parsed into individual factual propositions.
- **NLI Grounding Verification:** Every claim is evaluated against retrieved evidence anchors.
- **Uncertainty Refusal:** Any claim with grounding score $< 0.50$ is marked `UNSUPPORTED`. If Evidence Coverage drops below policy threshold (e.g., $70\%$), the response is blocked or routed to human review with explicit warning flags.
