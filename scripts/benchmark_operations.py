"""Post-selection operational comparison on training data only; no test outcomes used."""

import io
import json
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from bank_marketing.modeling.core import make_pipeline, scenarios

train = pd.read_csv("artifacts/training_reference.csv")
y = (train.y == "yes").astype(int)
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
rows = []
for scenario, features in scenarios(train.columns).items():
    for name, model in configs.items():
        pipe = make_pipeline(features, model)
        start = time.perf_counter()
        pipe.fit(train[features], y)
        fit = time.perf_counter() - start
        sample = train[features].iloc[:1]
        for _ in range(3):
            pipe.predict_proba(sample)
        wall = []
        cpu = []
        for _ in range(30):
            start = time.perf_counter()
            cpu_start = time.process_time()
            pipe.predict_proba(sample)
            wall.append(1000 * (time.perf_counter() - start))
            cpu.append(time.process_time() - cpu_start)
        buffer = io.BytesIO()
        joblib.dump(pipe, buffer)
        rows.append(
            dict(
                scenario=scenario,
                model=name,
                fit_seconds=fit,
                p95_ms=float(np.percentile(wall, 95)),
                cpu_seconds_per_1000=float(np.mean(cpu) * 1000),
                artifact_kib=buffer.tell() / 1024,
                explainability="élevée" if name.startswith(("dummy", "logreg")) else "moyenne",
                provider_dependency="aucune API externe",
                verdict="fuite — exclu" if scenario == "S1" else "non promu — audit requis",
            )
        )
        print(scenario, name, flush=True)
ops = pd.DataFrame(rows)
ops.to_csv("reports/operations_comparison.csv", index=False)
cv = pd.read_csv("reports/cv_comparison.csv")
cv.merge(ops, on=["scenario", "model"], suffixes=("_cv", "_fulltrain")).to_csv(
    "reports/scenario_arbitration.csv", index=False
)
Path("reports/operations_method.json").write_text(
    json.dumps(
        dict(
            purpose="Post-selection latency/cost comparison; 20 additional fits on training only, no model reselection",
            samples_per_model=30,
            parallelism=1,
            unit_cost="CPU seconds per 1000 sequential inferences, no monetary estimate",
            caveat="Local process measurements, not network, container or load performance",
        ),
        indent=2,
    )
    + "\n"
)
