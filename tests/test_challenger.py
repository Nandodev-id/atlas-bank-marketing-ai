import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "compare", Path(__file__).resolve().parents[1] / "scripts/compare_challenger.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_challenger_rejects_performance_regression(monkeypatch):
    results = iter(
        [
            dict(average_precision=0.5, brier=0.1, coverage=1, max_error_gap=0.1),
            dict(average_precision=0.3, brier=0.2, coverage=1, max_error_gap=0.1),
        ]
    )
    monkeypatch.setattr(module, "assess", lambda *args: next(results))
    outcome = module.compare({}, {}, None)
    assert not outcome["eligible_for_human_review"] and not outcome["automatic_promotion"]


def test_challenger_still_requires_human_review(monkeypatch):
    monkeypatch.setattr(
        module,
        "assess",
        lambda *args: dict(average_precision=0.5, brier=0.1, coverage=1, max_error_gap=0.1),
    )
    outcome = module.compare({}, {}, None)
    assert outcome["eligible_for_human_review"] and not outcome["automatic_promotion"]


def test_missing_fairness_evidence_blocks_promotion(monkeypatch):
    monkeypatch.setattr(
        module,
        "assess",
        lambda *args: dict(average_precision=0.5, brier=0.1, coverage=1, max_error_gap=None),
    )
    assert not module.compare({}, {}, None)["eligible_for_human_review"]
