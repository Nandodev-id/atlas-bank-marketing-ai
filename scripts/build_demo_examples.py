"""Examples selected from training to demonstrate branches, not to evaluate accuracy."""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from loguru import logger
from bank_marketing.modeling.core import predict_bundle
from bank_marketing.service.app import create_app

logger.remove()
b = joblib.load("artifacts/model.joblib")
train = pd.read_csv("artifacts/training_reference.csv")
p = predict_bundle(b, train)
cases = {}
for label, index in [("high", int(np.argmax(p))), ("low", int(np.argmin(p)))]:
    cases[label] = {"features": train[b["features"]].iloc[index].to_dict()}
cases["ood"] = json.loads(json.dumps(cases["high"]))
cases["ood"]["features"]["euribor3m"] = 99.0
responses = {}
with TestClient(create_app(db_path="runtime/demo-examples.sqlite", api_key="")) as client:
    for label, payload in cases.items():
        Path(f"reports/example_request_{label}.json").write_text(
            json.dumps(payload, indent=2) + "\n"
        )
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        responses[label] = response.json()
assert not responses["high"]["abstain"] and responses["high"]["prediction"] == "yes"
assert not responses["low"]["abstain"] and responses["low"]["prediction"] == "no"
assert responses["ood"]["abstain"] and responses["ood"]["probability"] is None
Path("reports/api_demo_cases.json").write_text(
    json.dumps(
        {
            "purpose": "Training examples, selected for API branch demonstration, not evaluation",
            "responses": responses,
        },
        indent=2,
    )
    + "\n"
)
print({k: (r["probability"], r["prediction"], r["abstain"]) for k, r in responses.items()})
