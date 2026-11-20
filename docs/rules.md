# MEDTRUST-ENGINE: Governing Engineering Rules & Operational Constraints

## 1. Zero Tolerance for Fake Functionality
- **No Mock or Simulated Returns:** Core RAG, retrieval, claim verification, risk evaluation, PII redaction, and security airlock must execute real algorithms.
- **No Hardcoded Answers:** Answers must originate strictly from retrieved evidence and model generation.
- **No Fake Metrics:** Latency must be measured via system clocks (`time.perf_counter()`), tokens must use provider reporting or local token counters, and scores must be mathematically derived.
- **No Fabricated Citations:** Every citation must map to an indexed chunk ID, page number, and content hash in the database.

## 2. Evidence Before Confidence Principle
- If retrieved evidence is below the configured confidence threshold or empty, the system must trigger an explicit `INSUFFICIENT_EVIDENCE` state and refuse unanchored definitive generation.
- Never hallucinate answers to please the user when documents do not support the query.

## 3. Privacy & Security Rules
- All untrusted input (documents and queries) must pass through the **Security Airlock** before processing.
- The **Privacy Shield** must detect and pseudonymize PII/PHI (18 HIPAA Safe Harbor identifiers) prior to dispatching prompts to LLMs or storing audit entries.
- Document content is treated strictly as **DATA**, never as executable instructions.
- API keys, credentials, and secrets must reside exclusively in backend environment variables and never be exposed in client bundles.

## 4. Architectural Boundaries
- Enforce strict separation: Presentation (React/TS) $\to$ API (FastAPI) $\to$ Services $\to$ Domain Logic $\to$ Infrastructure (SQLAlchemy, FAISS, BM25).
- Do not store master clinical data, embeddings, or audit logs in browser `localStorage`. Use PostgreSQL/SQLite backend persistence.

## 5. Medical Safety & Responsible Positioning
- Clearly display clinical decision-support disclaimers across all views.
- Do not claim autonomous diagnosis, treatment prescription, or legal compliance certifications without external validation.
