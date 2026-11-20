# MEDTRUST-ENGINE: Development & Operational Instructions

## 1. Operating Modes & Zero-G Metaphor
- Apply the **Zero-G / Anti-Gravity** conceptual layer for architecture and visualization (Evidence Gravity, Trust Orbit, Evidence Anchors, Security Airlock, Privacy Shield, Review Dock, Trust Trajectory, Knowledge Orbit).
- Maintain an austere, high-contrast, professional clinical enterprise UI (dark slate, crisp emerald, amber warnings, crimson alerts). No cartoonish space graphics, emojis, or gaming interfaces.

## 2. Iterative Vertical Slices Workflow
Implement in verified, working vertical slices:
1. **Slice 1 (Core Ingestion & Hybrid RAG):** PDF parsing $\to$ Semantic chunking $\to$ FAISS vector index + BM25 term index $\to$ RRF score fusion $\to$ Grounded generation with real citations.
2. **Slice 2 (Claim Verification Engine):** Atomic claim decomposition $\to$ NLI entailment scoring $\to$ Status classification (`SUPPORTED`, `PARTIAL`, `UNSUPPORTED`, `CONTRADICTED`) $\to$ Evidence Coverage % computation.
3. **Slice 3 (Query Risk Engine & Human Review):** 5-tier query risk taxonomy $\to$ Dynamic safety policy enforcement $\to$ Refusal on low support $\to$ Review Queue state machine.
4. **Slice 4 (Security Airlock & Privacy Shield):** Direct/Indirect prompt injection heuristics $\to$ Delimiter breakout isolation $\to$ HIPAA 18 PII detection & pseudonymization.
5. **Slice 5 (Governance, Audit & Evaluation Lab):** SHA-256 rolling chain hash audit ledger $\to$ NIST AI RMF mapping $\to$ 10-point automated benchmark suite.
6. **Slice 6 (Clinical Frontend SPA):** React 18 + TypeScript + Vite + Tailwind CSS + Lucide Icons + Recharts with 8 interactive pages.

## 3. Pluggable Providers & Fallbacks
- Support OpenAI, Anthropic, Gemini, Groq, and local models.
- If API keys are absent, activate the built-in **Deterministic Clinical Grounding Engine** to guarantee 100% offline functionality and testability.
