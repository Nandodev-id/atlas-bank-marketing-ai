"""Reconstruct the rejected sigmoid on calibration only, without touching fitted model or test."""

import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from bank_marketing.modeling.core import logit

b = joblib.load("artifacts/model.joblib")
splits = json.loads(Path("artifacts/split_indices.json").read_text())
df = pd.read_csv("data/raw/bank-additional-full.csv", sep=";").loc[splits["calibration"]]
p = b["pipeline"].predict_proba(df[b["features"]])[:, 1]
c = LogisticRegression(C=1e6, random_state=42).fit(logit(p), (df.y == "yes").astype(int))
Path("reports/calibration_audit.json").write_text(
    json.dumps(
        {
            "slope": float(c.coef_[0, 0]),
            "intercept": float(c.intercept_[0]),
            "retained": False,
            "reason": "Negative slope would reverse score ordering; rejected by original rule.",
        },
        indent=2,
    )
    + "\n"
)
print(c.coef_[0, 0])
