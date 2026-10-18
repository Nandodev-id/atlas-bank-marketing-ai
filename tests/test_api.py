import hashlib
import json
import uuid

import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from bank_marketing.modeling.core import make_pipeline
from bank_marketing.service.app import create_app


@pytest.fixture()
def model_dir(tmp_path):
    frame = pd.DataFrame({"default": ["no", "yes"] * 30, "euribor3m": np.linspace(0.1, 5, 60)})
    pipe = make_pipeline(list(frame), LogisticRegression()).fit(frame, [0, 1] * 30)
    bundle = dict(
        pipeline=pipe,
        calibrator=None,
        features=list(frame),
        threshold=0.5,
        reference={
            "default": {"kind": "categorical", "categories": ["no", "yes"]},
            "euribor3m": {"kind": "numeric", "minimum": 0.1, "maximum": 5.0, "median": 2.5},
        },
        version="test-v1",
        scenario="S4",
        model="test",
        abstention_margin=0.03,
    )
    folder = tmp_path / "model"
    folder.mkdir()
    joblib.dump(bundle, folder / "model.joblib")
    (folder / "model.sha256").write_text(
        hashlib.sha256((folder / "model.joblib").read_bytes()).hexdigest()
    )
    (folder / "metadata.json").write_text(json.dumps({"data_sha256": "different"}))
    frame.to_csv(folder / "training_reference.csv", index=False)
    return folder


@pytest.fixture()
def client(model_dir, tmp_path):
    with TestClient(create_app(model_dir, tmp_path / "audit.sqlite", api_key="test-key")) as c:
        c.headers["Authorization"] = "Bearer test-key"
        yield c


VALID = {"features": {"default": "no", "euribor3m": 2.0}}


def test_health_auth_and_probability_contract(client):
    assert client.get("/health").status_code == 200
    r = client.post("/predict", json=VALID)
    assert r.status_code == 200 and 0 <= r.json()["probability"] <= 1
    assert not r.json()["contact_authorized"]
    assert r.headers["x-request-id"] == r.json()["request_id"]
    client.headers.pop("Authorization")
    assert client.post("/predict", json=VALID).status_code == 401


@pytest.mark.parametrize(
    "features",
    [
        {"default": "no"},
        {"default": "no", "euribor3m": 2, "duration": 40},
        {"default": "bad", "euribor3m": 2},
        {"default": "no", "euribor3m": "2"},
        {"default": "no", "euribor3m": True},
        {"default": "no", "euribor3m": None},
    ],
)
def test_invalid_inputs(client, features):
    assert client.post("/predict", json={"features": features}).status_code == 422


def test_ood_abstains_without_extrapolated_probability(client):
    result = client.post(
        "/predict", json={"features": {"default": "unknown", "euribor3m": 99}}
    ).json()
    assert result["abstain"] and result["probability"] is None and result["prediction"] is None
    assert result["action"] == "human_review"


def test_feedback_is_linked_idempotent_and_conflicts_are_not_overwritten(client):
    prediction = client.post("/predict", json=VALID).json()
    feedback = {"request_id": prediction["request_id"], "outcome": "yes"}
    assert client.post("/feedback", json=feedback).status_code == 200
    assert client.post("/feedback", json=feedback).status_code == 200
    feedback["outcome"] = "no"
    assert client.post("/feedback", json=feedback).status_code == 409
    feedback["request_id"] = str(uuid.uuid4())
    assert client.post("/feedback", json=feedback).status_code == 404
    status = client.get("/monitoring").json()
    assert status["labeled"] == 1 and not status["retraining"]["retrain"]
    assert "atlas_requests_total" in client.get("/metrics").text


def test_training_requires_approved_snapshot(client, monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_TRAIN_DATA", str(tmp_path / "missing.csv"))
    assert client.post("/train", json={"reason": "new_labels"}).status_code == 409


def test_tampered_model_is_rejected(model_dir, tmp_path):
    (model_dir / "model.sha256").write_text("invalid")
    with pytest.raises(RuntimeError, match="integrity"):
        with TestClient(create_app(model_dir, tmp_path / "x.sqlite", api_key="test")):
            pass


def test_production_requires_auth(monkeypatch):
    monkeypatch.setenv("ATLAS_ENV", "production")
    with pytest.raises(RuntimeError, match="ATLAS_API_KEY"):
        create_app(api_key="")


def test_training_job_is_separate_from_champion(client, model_dir, tmp_path, monkeypatch):
    import subprocess
    import bank_marketing.service.app as module

    monkeypatch.chdir(tmp_path)
    source = tmp_path / "approved.csv"
    source.write_text("synthetic approved source; trainer mocked for lifecycle test")
    monkeypatch.setenv("ATLAS_TRAIN_DATA", str(source))
    before = (model_dir / "model.joblib").read_bytes()
    calls = []

    def complete(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(module.subprocess, "run", complete)
    result = client.post("/train", json={"reason": "new_labels"})
    assert result.status_code == 202
    job = client.get("/jobs/" + result.json()["job_id"]).json()
    assert job["status"] == "candidate_ready"
    assert "--artifacts" in calls[0] and "runtime/candidates/" in calls[0][-1]
    assert (model_dir / "model.joblib").read_bytes() == before


def test_nonfinite_value_rejected(client):
    response = client.post(
        "/predict",
        content='{"features":{"default":"no","euribor3m":NaN}}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
