"""Assess service coverage and subgroup gaps for a newly trained candidate."""

import argparse
import json
from pathlib import Path
import joblib
import pandas as pd
from bank_marketing.service.app import ood_reasons
from bank_marketing.modeling.core import fairness_gaps

p = argparse.ArgumentParser()
p.add_argument("--root", default=".")
p.add_argument("--data", default="data/raw/bank-additional-full.csv")
a = p.parse_args()
root = Path(a.root)
reports = root / "reports"
artifacts = root / "artifacts"
bundle = joblib.load(artifacts / "model.joblib")
splits = json.loads((artifacts / "split_indices.json").read_text())
data = pd.read_csv(a.data, sep=";").loc[splits["test"]]
pred = pd.read_csv(artifacts / "test_predictions.csv")
ood = [bool(ood_reasons(row, bundle)) for row in data[bundle["features"]].to_dict("records")]
accepted = [
    not flag and abs(p - bundle["threshold"]) > bundle["abstention_margin"]
    for flag, p in zip(ood, pred.probability)
]
fair = pd.read_csv(reports / "fairness_test.csv")
gaps = fairness_gaps(fair)
selection = json.loads((reports / "selection.json").read_text())
coverage = sum(accepted) / len(accepted)
checks = dict(
    validation_beats_prior=selection["validation"]["average_precision"]
    > selection["validation"]["prevalence"],
    coverage_at_least_80_percent=coverage >= 0.8,
    subgroup_error_gaps_under_20_points=all(
        gaps[k] is not None and gaps[k] <= 0.2 for k in ["fpr", "fnr"]
    ),
)
decision = dict(
    coverage=coverage,
    subgroup_gaps=gaps,
    checks=checks,
    production_gate_passed=all(checks.values()),
    thresholds="Educational review gates, not statutory fairness standards. Human approval still required.",
    recommendation="candidate_for_human_review" if all(checks.values()) else "do_not_deploy",
)
(reports / "production_decision.json").write_text(
    json.dumps(decision, indent=2, allow_nan=False) + "\n"
)
print(json.dumps(decision, indent=2, allow_nan=False))
