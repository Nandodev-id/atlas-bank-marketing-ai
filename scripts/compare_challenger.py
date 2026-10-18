"""Compare champion and challenger on an approved common labeled window.
No model fitting, no threshold tuning and no implicit promotion.
"""

import argparse
import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from bank_marketing.data.inspection import inspect_csv
from bank_marketing.modeling.core import metrics, predict_bundle, subgroup_metrics
from bank_marketing.service.app import ood_reasons
from bank_marketing.modeling.core import fairness_gaps


def assess(bundle, df):
    p = predict_bundle(bundle, df)
    result = metrics((df.y == "yes").astype(int), p, bundle["threshold"])
    ood = np.array(
        [bool(ood_reasons(r, bundle)) for r in df[bundle["features"]].to_dict("records")]
    )
    result["coverage"] = float(
        (~ood & (abs(p - bundle["threshold"]) > bundle["abstention_margin"])).mean()
    )
    fairness = subgroup_metrics(df, (df.y == "yes").astype(int), p, bundle["threshold"])
    gaps = fairness_gaps(fairness)
    result["max_error_gap"] = (
        max(gaps["fpr"], gaps["fnr"])
        if gaps["fpr"] is not None and gaps["fnr"] is not None
        else None
    )
    return result


def compare(champion, challenger, df):
    a, b = assess(champion, df), assess(challenger, df)
    passed = (
        b["average_precision"] >= a["average_precision"] - 0.01
        and b["brier"] <= a["brier"] + 0.01
        and b["coverage"] >= 0.8
        and b["max_error_gap"] is not None
        and b["max_error_gap"] <= 0.2
    )
    return dict(
        champion=a, challenger=b, eligible_for_human_review=bool(passed), automatic_promotion=False
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--champion", required=True)
    parser.add_argument("--challenger", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", default="reports/champion_challenger.json")
    args = parser.parse_args()
    inspect_csv(Path(args.data))
    df = pd.read_csv(args.data, sep=";")
    if len(df) < 200 or df.y.nunique() != 2:
        raise SystemExit("At least 200 labeled cases and both classes required")
    bundles = []
    for directory in [args.champion, args.challenger]:
        directory = Path(directory)
        blob = (directory / "model.joblib").read_bytes()
        assert hashlib.sha256(blob).hexdigest() == (directory / "model.sha256").read_text().strip()
        reference = pd.read_csv(directory / "training_reference.csv")
        columns = [c for c in df if c != "y"]
        seen = set(pd.util.hash_pandas_object(reference[columns], index=False))
        assert (
            not pd.util.hash_pandas_object(df[columns], index=False).isin(seen).any()
        ), "Evaluation overlaps training observations"
        bundles.append(joblib.load(directory / "model.joblib"))
    result = compare(*bundles, df)
    result["dataset_sha256"] = hashlib.sha256(Path(args.data).read_bytes()).hexdigest()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))
    if not result["eligible_for_human_review"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
