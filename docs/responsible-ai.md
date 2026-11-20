# MEDTRUST-ENGINE: Responsible AI, Governance & Safety Specification
**Document ID:** GOV-MEDTRUST-2026-V1.0  
**Status:** Approved for Implementation  
**Classification:** Responsible AI Framework & Risk Controls  
**Frameworks:** NIST AI RMF 1.0 | EU AI Act (High-Risk AI Safety Concepts)

---

## 1. Intended Use & Operational Scope

### 1.1 Intended Use
MedTrust-Engine is designed exclusively as an **evidence-grounded clinical AI verification and decision-support platform** for licensed physicians, clinical researchers, quality assurance reviewers, and health informatics teams. It assists in:
- Rapid semantic search across institutional clinical protocols and national guidelines.
- Grounding verification of clinical statements against specific, versioned source pages.
- Detecting version conflicts and discrepancies across evolving guidelines.
- Pre-screening clinical queries and documents for PHI/PII and adversarial prompt injections.
- Maintaining a tamper-evident audit trail for clinical governance.

### 1.2 Prohibited Use
MedTrust-Engine is **strictly prohibited** from:
- Autonomous diagnosis of medical conditions.
- Autonomous prescription or calculation of medication doses without clinician validation.
- Direct automated execution of medical orders or EHR write-back without human review.
- Emergency triage where latency $< 100\text{ms}$ is required.
- Commercial marketing as a certified medical device without prior regulatory clearance.

---

## 2. Medical Safety Disclaimer

> [!WARNING]
> **RESEARCH & CLINICAL DECISION-SUPPORT SYSTEM ONLY:**  
> MedTrust-Engine is not an autonomous diagnostic device, certified medical device, or replacement for qualified clinical judgment. Clinicians must independently evaluate all evidence citations, verify recommended drug dosages against official pharmacopeia, and exercise licensed medical judgment before initiating patient care.

---

## 3. NIST AI Risk Management Framework (AI RMF 1.0) Mapping

```
+---------------------------------------------------------------------------------------------------------------+
|                                    NIST AI RMF 1.0 CONTROL MAPPING                                            |
+-------------------+---------------------------------------+---------------------------------------------------+
| NIST Function     | MedTrust Platform Control             | Verification Metric / Artifact                    |
+-------------------+---------------------------------------+---------------------------------------------------+
| **GOVERN**        | Human-in-the-loop Review Queue Dock   | Reviewer decision audit logs, escalation trails   |
| (1.1, 1.2)        | Role-based oversight policies         | Distinct AI-generated vs Human-approved state     |
+-------------------+---------------------------------------+---------------------------------------------------+
| **MAP**           | 5-Tier Query Risk Classification      | Risk tier tagging (`INFORMATIONAL` to `PATIENT`)  |
| (2.1, 2.3)        | Threat modeling (OWASP Top 10 for LLM)| Threat matrix (`docs/threat-model.md`)            |
+-------------------+---------------------------------------+---------------------------------------------------+
| **MEASURE**       | Multi-dimensional Trust Profile       | Evidence Coverage %, Grounding Score, Retrieval Q |
| (3.1, 3.2)        | Evaluation Lab automated benchmark    | 10-point test suite, Refusal F1, Latency tracking |
+-------------------+---------------------------------------+---------------------------------------------------+
| **MANAGE**        | Security Airlock (Injection defense)  | Quarantined documents, blocked security events    |
| (4.1, 4.2)        | Privacy Shield (HIPAA 18 redactions)  | Pseudonymization logs, zero raw PII in prompts    |
|                   | Insufficient Evidence Refusal Engine  | Epistemic refusal when corpus coverage $< 65\%$   |
+-------------------+---------------------------------------+---------------------------------------------------+
```

---

## 4. EU AI Act Alignment Considerations (High-Risk AI Concepts)

While MedTrust is a prototype/research platform and does not claim official legal certification, its design incorporates core structural tenets of the EU AI Act for High-Risk AI Systems:
1. **Risk Management System (Article 9):** Continuous evaluation of epistemic uncertainty and dynamic escalation of dosage/treatment queries.
2. **Data Governance & Provenance (Article 10):** Structured semantic chunking with SHA-256 content hashes, version lineage, and superseded document deprecation.
3. **Technical Documentation (Article 11):** Comprehensive architectural, data model, threat model, and evaluation specifications.
4. **Record-Keeping & Logging (Article 12):** Cryptographically chained SHA-256 rolling audit ledger recording all queries, responses, model metadata, and reviewer actions.
5. **Transparency & Explainability (Article 13):** Visual **Trust Trajectory** detailing every pipeline stage and claim-level evidence links.
6. **Human Oversight (Article 14):** Interactive **Review Queue** allowing clinical reviewers to approve, edit, reject, or escalate risky outputs.
7. **Accuracy, Robustness & Cybersecurity (Article 15):** Hybrid dense+sparse retrieval, prompt-injection airlocks, and graceful offline fallback modes.

---

## 5. Failure Modes & Safe Fallback Behaviors

| Subsystem Failure | Impact | Failure-Safe System Action | User Communication |
|:---|:---|:---|:---|
| **External LLM Outage** | Generation unavailable | Activate Deterministic Extractive Clinical Engine | *"External AI service unavailable. Showing verified extractive evidence quotes."* |
| **Vector DB Unavailable** | Dense search fails | Fall back to Sparse BM25 Term Retrieval | *"Vector index unreachable. Performing exact clinical keyword search."* |
| **Low Evidence Yield** | Query not in corpus | Trigger `INSUFFICIENT_EVIDENCE` refusal state | *"Corpus lacks sufficient evidence. Generation restricted to prevent hallucination."* |
| **Corrupt / Malicious PDF**| Document unparseable | Security Airlock quarantines file | *"Document validation failed or injection detected. File isolated safely."* |
| **Verification Anomaly** | NLI matcher times out | Mark claims `UNABLE_TO_VERIFY` + enqueue | *"Verification uncertain. Routed to human clinical review queue."* |
