# Atlas Bank Marketing AI

A reproducible, responsible AI project for **bank term-deposit marketing targeting**, developed for the Simplon / OPCO Atlas **Concevoir et implémenter une solution d'IA** certification (C1–C9).

> **Status: Session 1 — project foundation.** No model has been trained, no predictions have been validated, and no banking system has been integrated. Never use this starter to make real customer decisions.

## Problem

Predict whether a contacted customer will subscribe to a term deposit while analyzing feature leakage, fairness, time-related shift, and operational constraints. The file `bank-additional-full.csv` contains **41,188 observations**, **20 predictors**, and the binary outcome `y` (`yes`/`no`).

## Quick start (Mac, Python 3.11–3.13)

```bash
cd ~/path/to/ia/atlas-bank-marketing-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m bank_marketing.data.inspection
python -m pytest -q
```

The raw CSV is supplied in the downloadable starter ZIP. It is intentionally `.gitignore`d; obtain the original from the [UCI Bank Marketing dataset](https://archive.ics.uci.edu/dataset/222/bank+marketing) if you clone GitHub without that ZIP. Verify the file using `data/raw/DATASET.sha256`.

Optional: run `python scripts/fetch_simplon_canvas.py` on your Mac to obtain the complete official course canvas as a separate reference notebook.

To install future API/MLOps dependencies, use the optional dependency groups in `pyproject.toml` when those phases begin.

## Structure

- `notebooks/certification.ipynb` — nine-section certification notebook **based on** Simplon's published canvas (not a verbatim copy).
- `notebooks/exploration.ipynb` — EDA starter; no model training yet.
- `src/bank_marketing/data` — source data contract and read-only inspection.
- `src/bank_marketing/modeling`, `ethics`, `monitoring` — modules reserved for future phases.
- `api/`, `tests/`, `.github/workflows/` — serving, verification and CI/CD.
- `docs/` — approved plan, evidence and design decisions.

## Approved engineering principles (Plan v2)

1. Define the **pre-contact decision point** and audit feature availability.
2. Include S1 (all features; leakage illustration), S2 (without `duration`), S3 (fairness-related exclusions), and S4 (minimal, if feasible).
3. Make **chronological, out-of-time assessment** primary; retain a sealed holdout.
4. Compare Logistic Regression and Random Forest, with optional Gradient Boosting.
5. Evaluate ranking utility and calibration, not accuracy alone.
6. Measure subgroup fairness, secure personal data, and promote models only through release gates.

**Important:** the dataset is reportedly chronologically ordered but lacks full per-row timestamps and customer IDs. We must verify these assumptions before finalizing the validation protocol. No causal claim about marketing-call effectiveness can be made from this observational table alone.

## Source materials

See [docs/SOURCES.md](docs/SOURCES.md), [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) and [docs/SESSION_01.md](docs/SESSION_01.md).
