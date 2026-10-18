# Architecture Decision Record

## ADR-001 — Source control and runtime separation

**Status:** accepted, 2026-10-16.

Git stores code, tests, manifest and documentation. The learner's Mac holds the editable working tree and the original public CSV. The CSV and runtime model artifacts are ignored by Git until data-governance and release policies are approved.

## ADR-002 — Classic supervised ML before advanced AI

**Status:** accepted, 2026-10-16.

Use scikit-learn's Logistic Regression and Random Forest. Consider Gradient Boosting only if it earns measurable improvement without unacceptable added cost, explainability or maintenance burden. Do not use LLM/RAG/agents for this binary tabular classification.

## ADR-003 — Primary temporal robustness testing

**Status:** accepted in principle; exact split configuration must be finalized after auditing source order.

Use a sealed chronological holdout and time-aware model selection; report limitations of missing complete timestamps and customer IDs. Keep a secondary stratified random benchmark for comparability.

## ADR-004 — Separation of experimentation and serving

**Status:** accepted, 2026-10-16.

Reusable transformations and model behavior must be implemented in Python modules. Notebooks present decisions and evidence, and the API loads a versioned complete pipeline. No notebook-dependent service code.
