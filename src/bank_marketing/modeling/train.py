"""Run the registered experiment. Refuses to overwrite a completed final assessment."""

import argparse
import hashlib
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, TimeSeriesSplit, cross_val_score
from .core import (
    NUMERIC,
    logit,
    make_pipeline,
    metrics,
    predict_bundle,
    scenarios,
    subgroup_metrics,
)
from bank_marketing.data.inspection import inspect_csv


def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def clean_later(earlier, later):
    columns = [c for c in earlier.columns if c != "y"]
    seen = set(pd.util.hash_pandas_object(earlier[columns], index=False))
    keep = ~pd.util.hash_pandas_object(later[columns], index=False).isin(seen)
    return later.loc[keep]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/raw/bank-additional-full.csv")
    parser.add_argument("--output", default="reports")
    parser.add_argument("--artifacts", default="artifacts")
    args = parser.parse_args()
    output, artifacts = Path(args.output), Path(args.artifacts)
    output.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    if (output / "final_test.json").exists():
        raise SystemExit(
            "Final test already evaluated. Use a new output directory and document the rerun."
        )
    protocol = json.loads(Path("config/protocol.json").read_text())
    inspect_csv(Path(args.data))
    data = pd.read_csv(args.data, sep=";")
    if len(data) < 1000 or data.y.nunique() != 2:
        raise ValueError("Training requires at least 1000 rows and both target classes")
    n = len(data)
    a, b, c = int(0.6 * n), int(0.7 * n), int(0.8 * n)
    train = data.iloc[:a].copy()
    calibration = clean_later(train, data.iloc[a:b]).copy()
    validation = clean_later(data.iloc[:b], data.iloc[b:c]).copy()
    test_indices = clean_later(data.iloc[:c], data.iloc[c:]).index
    # Test outcomes are not read until after selection, calibration and threshold freezing.
    splits = dict(
        train=train.index.tolist(),
        calibration=calibration.index.tolist(),
        validation=validation.index.tolist(),
        test=test_indices.tolist(),
    )
    save_json(artifacts / "split_indices.json", splits)
    save_json(output / "protocol.json", protocol)
    train.to_csv(artifacts / "training_reference.csv", index=False)
    feature_sets = scenarios(data.columns)
    y = (train.y == "yes").astype(int)
    cv = TimeSeriesSplit(n_splits=3, gap=100)
    configs = {
        "dummy": DummyClassifier(strategy="prior"),
        "logreg_C0.1": LogisticRegression(C=0.1, max_iter=2000, random_state=42),
        "logreg_C1": LogisticRegression(C=1, max_iter=2000, random_state=42),
        "rf_depth8": RandomForestClassifier(
            n_estimators=100, max_depth=8, min_samples_leaf=10, n_jobs=1, random_state=42
        ),
        "rf_depth16": RandomForestClassifier(
            n_estimators=100, max_depth=16, min_samples_leaf=5, n_jobs=1, random_state=42
        ),
    }
    folds, rows = [], []
    for scenario, features in feature_sets.items():
        for name, estimator in configs.items():
            for fold, (tr, va) in enumerate(cv.split(train), 1):
                tr_frame = train.iloc[tr]
                va_frame = clean_later(tr_frame, train.iloc[va])
                pipe = make_pipeline(features, estimator)
                start = time.perf_counter()
                pipe.fit(tr_frame[features], (tr_frame.y == "yes").astype(int))
                elapsed = time.perf_counter() - start
                p = pipe.predict_proba(va_frame[features])[:, 1]
                m = metrics((va_frame.y == "yes").astype(int), p)
                folds.append(
                    dict(
                        scenario=scenario,
                        model=name,
                        fold=fold,
                        n_train=len(tr_frame),
                        train_end=int(tr_frame.index.max()),
                        validation_start=int(va_frame.index.min()),
                        fit_seconds=elapsed,
                        **m,
                    )
                )
            subset = [r for r in folds if r["scenario"] == scenario and r["model"] == name]
            row = dict(scenario=scenario, model=name, n_features=len(features))
            for key in [
                "average_precision",
                "roc_auc",
                "f1",
                "precision",
                "recall",
                "brier",
                "precision_at_20",
                "lift_at_20",
                "fit_seconds",
            ]:
                row[key] = float(np.mean([r[key] for r in subset]))
                row[key + "_std"] = float(np.std([r[key] for r in subset]))
            rows.append(row)
            print(f"{scenario} {name}: CV AP={row['average_precision']:.4f}", flush=True)
    comparison = pd.DataFrame(rows)
    pd.DataFrame(folds).to_csv(output / "cv_folds.csv", index=False)
    comparison.to_csv(output / "cv_comparison.csv", index=False)
    eligible = comparison[(comparison.scenario != "S1") & (comparison.model != "dummy")]
    near_best = eligible[eligible.average_precision >= eligible.average_precision.max() - 0.02]
    winner = near_best.sort_values(
        ["n_features", "average_precision", "fit_seconds"], ascending=[True, False, True]
    ).iloc[0]
    scenario, name = winner.scenario, winner.model
    features = feature_sets[scenario]
    pipe = make_pipeline(features, configs[name])
    start = time.perf_counter()
    pipe.fit(train[features], y)
    fit_seconds = time.perf_counter() - start
    yc = (calibration.y == "yes").astype(int)
    yv = (validation.y == "yes").astype(int)
    raw_c = pipe.predict_proba(calibration[features])[:, 1]
    raw_v = pipe.predict_proba(validation[features])[:, 1]
    calibrator = LogisticRegression(C=1e6, random_state=42).fit(logit(raw_c), yc)
    calibrated_v = calibrator.predict_proba(logit(raw_v))[:, 1]
    use_calibration = (
        metrics(yv, calibrated_v)["brier"] < metrics(yv, raw_v)["brier"]
        and calibrator.coef_[0, 0] > 0
    )
    pv = calibrated_v if use_calibration else raw_v
    candidates = [(metrics(yv, pv, float(t))["f1"], float(t)) for t in np.arange(0.05, 0.801, 0.01)]
    _, threshold = max(candidates)
    val_metrics = metrics(yv, pv, threshold)
    bundle = dict(
        pipeline=pipe,
        calibrator=calibrator if use_calibration else None,
        features=features,
        scenario=scenario,
        model=name,
        threshold=threshold,
    )
    # Metadata and fallback reference are learned on training only.
    reference = {}
    for col in features:
        if col in NUMERIC:
            reference[col] = dict(
                kind="numeric",
                minimum=float(train[col].min()),
                maximum=float(train[col].max()),
                median=float(train[col].median()),
            )
        else:
            reference[col] = dict(
                kind="categorical", categories=sorted(train[col].unique().tolist())
            )
    bundle["reference"] = reference
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle["version"] = version
    bundle["abstention_margin"] = 0.03
    save_json(
        output / "selection.json",
        dict(
            scenario=scenario,
            model=name,
            features=features,
            threshold=threshold,
            calibrated=bool(use_calibration),
            raw_validation_brier=metrics(yv, raw_v)["brier"],
            calibrated_validation_brier=metrics(yv, calibrated_v)["brier"],
            calibration_slope=float(calibrator.coef_[0, 0]),
            validation=val_metrics,
            cv_average_precision=float(winner.average_precision),
            rule=protocol["selection_rule"],
            frozen_before_test=True,
        ),
    )
    # Secondary random-CV benchmark ONLY within the original training block.
    random_cv = cross_val_score(
        make_pipeline(features, configs[name]),
        train[features],
        y,
        cv=StratifiedKFold(3, shuffle=True, random_state=42),
        scoring="average_precision",
    )
    save_json(
        output / "random_cv_sensitivity.json",
        dict(
            scores=random_cv.tolist(),
            mean=float(random_cv.mean()),
            note="Training block only; duplicates retained here; optimistic sensitivity, not primary result.",
        ),
    )
    permutation = permutation_importance(
        pipe,
        validation[features],
        yv,
        scoring="average_precision",
        n_repeats=3,
        random_state=42,
        n_jobs=1,
    )
    pd.DataFrame(
        dict(
            feature=features,
            importance=permutation.importances_mean,
            std=permutation.importances_std,
        )
    ).sort_values("importance", ascending=False).to_csv(
        output / "permutation_importance.csv", index=False
    )
    subgroup_metrics(validation, yv, pv, threshold).to_csv(
        output / "fairness_validation.csv", index=False
    )
    # Single opening of final test after choices are persisted.
    test = data.loc[test_indices]
    yt = (test.y == "yes").astype(int)
    pt = predict_bundle(bundle, test)
    final = metrics(yt, pt, threshold)
    baseline = metrics(yt, np.full(len(yt), float(y.mean())))
    subgroup_metrics(test, yt, pt, threshold).to_csv(output / "fairness_test.csv", index=False)
    pred_frame = pd.DataFrame(dict(row_index=test.index, y=yt, probability=pt))
    pred_frame.to_csv(artifacts / "test_predictions.csv", index=False)
    pd.DataFrame(dict(row_index=validation.index, y=yv, probability=pv)).to_csv(
        artifacts / "validation_predictions.csv", index=False
    )
    # Bootstrap describes sampling uncertainty, not temporal drift uncertainty.
    rng = np.random.default_rng(42)
    ap_samples = []
    for _ in range(200):
        indices = rng.integers(0, len(yt), len(yt))
        ap_samples.append(metrics(yt.iloc[indices], pt[indices], threshold)["average_precision"])
    timings = []
    for _ in range(5):
        predict_bundle(bundle, train.iloc[:1])
    for _ in range(100):
        start = time.perf_counter()
        predict_bundle(bundle, train.iloc[:1])
        timings.append((time.perf_counter() - start) * 1000)
    final["model_latency_p95_ms"] = float(np.percentile(timings, 95))
    final["ap_bootstrap_95_ci"] = np.quantile(ap_samples, [0.025, 0.975]).tolist()
    final["baseline"] = baseline
    final["test_openings"] = 1
    final["local_gate_passed"] = bool(
        final["average_precision"] > final["prevalence"]
        and final["roc_auc"] >= 0.6
        and final["lift_at_20"] >= 1.2
        and final["model_latency_p95_ms"] < 500
    )
    final["production_approved"] = False
    save_json(output / "final_test.json", final)
    joblib.dump(bundle, artifacts / "model.joblib")
    sha = hashlib.sha256((artifacts / "model.joblib").read_bytes()).hexdigest()
    (artifacts / "model.sha256").write_text(sha + "\n")
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit = "unavailable"
    meta = dict(
        version=version,
        scenario=scenario,
        model=name,
        features=features,
        threshold=threshold,
        model_sha256=sha,
        data_sha256=hashlib.sha256(Path(args.data).read_bytes()).hexdigest(),
        python=platform.python_version(),
        sklearn=sklearn.__version__,
        git_commit=commit,
        git_dirty=bool(subprocess.check_output(["git", "status", "--porcelain"], text=True)),
        split_sizes={k: len(v) for k, v in splits.items()},
        fit_seconds=fit_seconds,
        platform=platform.platform(),
        production_approved=False,
    )
    bundle_example = {
        k: (float(v) if isinstance(v, (np.floating, np.integer)) else v)
        for k, v in train[features].iloc[0].to_dict().items()
    }
    save_json(output / "example_request.json", dict(features=bundle_example))
    save_json(artifacts / "metadata.json", meta)
    save_json(output / "metadata.json", meta)
    # Local experiment tracking; no remote account or network.
    import mlflow

    mlflow.set_tracking_uri(Path("mlruns").resolve().as_uri())
    mlflow.set_experiment("atlas-bank-marketing")
    with mlflow.start_run(run_name=f"{scenario}-{name}-{version}") as run:
        mlflow.log_params(
            dict(
                scenario=scenario,
                model=name,
                threshold=threshold,
                seed=42,
                calibration=use_calibration,
                data_sha256=meta["data_sha256"],
            )
        )
        mlflow.log_metrics({k: float(v) for k, v in final.items() if type(v) in (int, float)})
        mlflow.log_artifacts(str(output), artifact_path="reports")
        mlflow.log_artifact(str(artifacts / "model.joblib"), artifact_path="model")
        save_json(
            output / "mlflow_run.json",
            dict(run_id=run.info.run_id, tracking_uri=mlflow.get_tracking_uri()),
        )
    print(json.dumps(dict(selected=f"{scenario}/{name}", test=final), indent=2), flush=True)


if __name__ == "__main__":
    main()
