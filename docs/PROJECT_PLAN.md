# Approved architecture baseline — v2

Approval: learner approved in chat on 2026-10-16. Implementation begins with Session 1.

## Delivery stages and CISIA competencies

| Stage | Evidence | Main competencies |
| --- | --- | --- |
| 1. Framing | Business objective, prediction moment, risks, KPIs | C1, C2, C4 |
| 2. EDA | Schema, quality, imbalance, exploratory findings | C1, C2, C3 |
| 3. Preparation | Train-only fitted transformations, reproducible pipeline | C3 |
| 4. Benchmarking | Dummy, logistic regression, random forest, conditional challenger | C4, C5 |
| 5. Responsible selection | Feature scenarios S1-S4, fairness, calibration, cost, errors | C2, C4, C5 |
| 6. Serving | FastAPI /predict, /health, protected /train design, tests | C6, C7 |
| 7. Deployment | Docker, CI/CD, secure hosting proposal, load evaluation | C6, C7, C9 |
| 8. Operations | Observability, drift, feedback, gated retraining, rollback | C8, C9 |
| 9. Certification | Complete notebook and jury materials | C1-C9 |

## Scientific safeguards

- Establish **when** a prediction is made, and prevent post-outcome features from entering deployable scenarios.
- Respect original row order during **chronological** validation; assess temporal-order limitations explicitly.
- Keep the final holdout sealed until a model, operating point and feature set have been chosen.
- Treat scenario S1 (`duration` included) as a **leakage demonstration** only.
- Use the same evaluation framework across scenarios, record model/data/code versions.
- Treat feature exclusion and fairness evaluation as separate activities.
- Use a source-data audit dataset where appropriate, not sensitive attributes in deployed predictor inputs by default.
- Propose and test an API contract only after model selection; no automatic promotion after a retraining run.

## Infrastructure roadmap

Python / scikit-learn -> MLflow experiment tracking -> validated FastAPI service -> Docker -> GitHub Actions -> Prometheus/Grafana. Prefer CPU-first and no Kubernetes for this scope.

## Acceptance gates

Every stage requires runnable evidence, clear limitations, and documentation. Business success thresholds must be defined from stakeholder assumptions and training-only feasibility checks, **not** tuned after final test inspection.
