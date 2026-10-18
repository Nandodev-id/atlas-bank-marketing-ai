"""FastAPI factory: no training, credentials or model loading at import time."""

import hashlib
import json
import math
import os
import secrets
import subprocess
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
import pandas as pd
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from loguru import logger
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr

from bank_marketing.modeling.core import NUMERIC, predict_bundle
from bank_marketing.monitoring.checks import drift_report, retraining_decision
from .store import Store

CATEGORIES = {
    "job": [
        "admin.",
        "blue-collar",
        "entrepreneur",
        "housemaid",
        "management",
        "retired",
        "self-employed",
        "services",
        "student",
        "technician",
        "unemployed",
        "unknown",
    ],
    "marital": ["divorced", "married", "single", "unknown"],
    "education": [
        "basic.4y",
        "basic.6y",
        "basic.9y",
        "high.school",
        "illiterate",
        "professional.course",
        "university.degree",
        "unknown",
    ],
    "default": ["yes", "no", "unknown"],
    "housing": ["yes", "no", "unknown"],
    "loan": ["yes", "no", "unknown"],
    "contact": ["cellular", "telephone"],
    "month": ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
    "day_of_week": ["mon", "tue", "wed", "thu", "fri"],
    "poutcome": ["failure", "nonexistent", "success"],
}


class PredictionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: dict[str, StrictFloat | StrictInt | StrictStr] = Field(min_length=1, max_length=20)


class FeedbackInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: uuid.UUID
    outcome: Literal["yes", "no"]


class TrainInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: Literal["scheduled", "performance_drop", "new_labels"]


def validate_features(features, bundle):
    expected = set(bundle["features"])
    if set(features) != expected:
        raise HTTPException(
            422,
            detail=dict(
                message="Exact model feature set required",
                missing=sorted(expected - set(features)),
                extra=sorted(set(features) - expected),
            ),
        )
    clean = {}
    for col, value in features.items():
        if col in NUMERIC:
            if (
                isinstance(value, (bool, str))
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise HTTPException(422, f"{col}: finite numeric value required")
            if col in ["age", "campaign", "pdays", "previous"] and (
                value < 0 or value != int(value)
            ):
                raise HTTPException(422, f"{col}: non-negative integer required")
            if col == "age" and not 18 <= value <= 120:
                raise HTTPException(422, "age: adult clients only (18..120)")
            if col == "campaign" and value < 1:
                raise HTTPException(422, "campaign: ordinal of planned contact must be >=1")
            clean[col] = float(value)
        else:
            if not isinstance(value, str) or value not in CATEGORIES[col]:
                raise HTTPException(422, f"{col}: unsupported category")
            clean[col] = value
    return clean


def ood_reasons(features, bundle):
    reasons = []
    for col, value in features.items():
        ref = bundle["reference"][col]
        if ref["kind"] == "numeric" and not ref["minimum"] <= value <= ref["maximum"]:
            reasons.append(f"out_of_range:{col}")
        if ref["kind"] == "categorical" and value not in ref["categories"]:
            reasons.append(f"unseen_category:{col}")
    return reasons


def create_app(model_dir=None, db_path=None, api_key=None):
    model_dir = Path(model_dir or os.getenv("ATLAS_MODEL_DIR", "artifacts"))
    key = api_key if api_key is not None else os.getenv("ATLAS_API_KEY", "")
    if os.getenv("ATLAS_ENV", "demo") == "production" and not key:
        raise RuntimeError("ATLAS_API_KEY is required in production")
    registry = CollectorRegistry()
    requests = Counter(
        "atlas_requests_total", "HTTP responses", ["route", "status"], registry=registry
    )
    latency = Histogram("atlas_request_seconds", "HTTP latency", ["route"], registry=registry)
    abstentions = Counter("atlas_abstentions_total", "Abstentions", registry=registry)
    lock = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        bundle_path = model_dir / "model.joblib"
        if not bundle_path.is_file():
            raise RuntimeError("Run training before starting the API")
        expected = (model_dir / "model.sha256").read_text().strip()
        if hashlib.sha256(bundle_path.read_bytes()).hexdigest() != expected:
            raise RuntimeError("Model integrity mismatch")
        app.state.bundle = joblib.load(bundle_path)  # trusted local artifact only
        if "duration" in app.state.bundle["features"]:
            raise RuntimeError("Leakage scenario cannot be served")
        app.state.store = Store(db_path or os.getenv("ATLAS_DB_PATH", "runtime/audit.sqlite"))
        app.state.started = time.time()
        reference_path = model_dir / "training_reference.csv"
        app.state.reference = pd.read_csv(reference_path) if reference_path.exists() else None
        yield

    app = FastAPI(
        title="Atlas — Marketing bancaire responsable",
        version="1.0.0",
        lifespan=lifespan,
        description="Prototype pédagogique. Un score ne constitue pas une autorisation de démarchage.",
    )

    def auth(authorization: str | None = Header(default=None)):
        if key and (
            authorization is None or not secrets.compare_digest(authorization, "Bearer " + key)
        ):
            raise HTTPException(401, "Authentication required")

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {"loc": list(e["loc"]), "type": e["type"], "msg": e["msg"]}
                    for e in exc.errors()
                ]
            },
        )

    @app.middleware("http")
    async def telemetry(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request.state.request_id
            return response
        finally:
            route = getattr(request.scope.get("route"), "path", "unmatched")
            duration = time.perf_counter() - start
            requests.labels(route, str(status)).inc()
            latency.labels(route).observe(duration)
            # No request bodies, bearer token, or personal values in application logs.
            logger.bind(
                request_id=request.state.request_id,
                route=route,
                status=status,
                elapsed_ms=round(duration * 1000, 3),
            ).info("request_completed")

    @app.get("/health")
    def health():
        return dict(
            status="ok", model_version=app.state.bundle["version"], production_approved=False
        )

    @app.get("/model", dependencies=[Depends(auth)])
    def model():
        b = app.state.bundle
        return {
            k: b[k] for k in ["version", "features", "scenario", "model", "threshold", "reference"]
        }

    @app.post("/predict", dependencies=[Depends(auth)])
    def predict(payload: PredictionInput, request: Request):
        b = app.state.bundle
        features = validate_features(payload.features, b)
        reasons = ood_reasons(features, b)
        probability = None
        if not reasons:
            probability = float(predict_bundle(b, pd.DataFrame([features]))[0])
            if abs(probability - b["threshold"]) <= b["abstention_margin"]:
                reasons.append("near_decision_threshold")
        abstain = bool(reasons)
        if abstain:
            abstentions.inc()
        prediction = None if abstain else ("yes" if probability >= b["threshold"] else "no")
        app.state.store.prediction(
            request.state.request_id, b["version"], probability, abstain, features
        )
        return dict(
            request_id=request.state.request_id,
            model_version=b["version"],
            probability=probability,
            prediction=prediction,
            threshold=b["threshold"],
            abstain=abstain,
            reasons=reasons,
            action="human_review" if abstain else "decision_support_only",
            contact_authorized=False,
        )

    @app.post("/feedback", dependencies=[Depends(auth)])
    def feedback(payload: FeedbackInput):
        result = app.state.store.feedback(str(payload.request_id), int(payload.outcome == "yes"))
        if result == "missing":
            raise HTTPException(404, "Unknown or expired prediction")
        if result == "conflict":
            raise HTTPException(409, "Conflicting feedback requires an audited correction")
        return dict(status="recorded", used_for_automatic_training=False)

    @app.get("/monitoring", dependencies=[Depends(auth)])
    def monitoring():
        b = app.state.bundle
        rows = app.state.store.rows(b["version"])
        labels = [r for r in rows if r["outcome"] is not None and r["probability"] is not None]
        drift = []
        if len(rows) >= 100 and app.state.reference is not None:
            current = pd.DataFrame([json.loads(r["features"]) for r in rows])
            drift = drift_report(app.state.reference, current, b["features"])
        selection_path = model_dir.parent / "reports/selection.json"
        baseline_ap = 0.2
        if selection_path.exists():
            baseline_ap = json.loads(selection_path.read_text())["validation"]["average_precision"]
        decision = retraining_decision(
            [r["outcome"] for r in labels],
            [r["probability"] for r in labels],
            baseline_ap,
            any(r["alert"] for r in drift),
        )
        return dict(
            model_version=b["version"],
            requests=len(rows),
            labeled=len(labels),
            abstention_rate=sum(r["abstain"] for r in rows) / len(rows) if rows else None,
            label_coverage=len(labels) / len(rows) if rows else None,
            uptime_seconds=time.time() - app.state.started,
            drift=drift,
            retraining=decision,
            caveat="Feedback is observational and potentially selectively labeled; audit sampling is required.",
        )

    @app.get("/metrics", dependencies=[Depends(auth)])
    def prometheus():
        return Response(generate_latest(registry), media_type="text/plain; version=0.0.4")

    def train_candidate(job_id, source):
        try:
            root = Path("runtime/candidates") / job_id
            root.mkdir(parents=True, exist_ok=True)
            app.state.store.job(job_id, "running", "Candidate training; champion unchanged")
            with (root / "training.log").open("w") as log:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "bank_marketing.modeling.train",
                        "--data",
                        str(source),
                        "--output",
                        str(root / "reports"),
                        "--artifacts",
                        str(root / "artifacts"),
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=1800,
                    check=False,
                )
            app.state.store.job(
                job_id,
                "candidate_ready" if result.returncode == 0 else "failed",
                "Human review required; no automatic promotion",
            )
        except Exception:
            app.state.store.job(job_id, "failed", "Training error; consult restricted job log")
        finally:
            lock.release()

    @app.post("/train", status_code=202, dependencies=[Depends(auth)])
    def train(payload: TrainInput, background: BackgroundTasks):
        # Even an unauthenticated local demo cannot initiate training without an admin key.
        if not key:
            raise HTTPException(503, "Configure ATLAS_API_KEY before enabling training")
        source = Path(os.getenv("ATLAS_TRAIN_DATA", "runtime/approved_training.csv"))
        if not source.is_file():
            raise HTTPException(409, "No approved training snapshot available")
        meta = json.loads((model_dir / "metadata.json").read_text())
        if hashlib.sha256(source.read_bytes()).hexdigest() == meta["data_sha256"]:
            raise HTTPException(
                409, "New approved data required; do not reuse the final examination holdout"
            )
        if not lock.acquire(blocking=False):
            raise HTTPException(409, "Training already running")
        job_id = str(uuid.uuid4())
        app.state.store.job(job_id, "queued", payload.reason)
        background.add_task(train_candidate, job_id, source)
        return dict(job_id=job_id, status="queued", automatic_promotion=False)

    @app.get("/jobs/{job_id}", dependencies=[Depends(auth)])
    def job(job_id: uuid.UUID):
        result = app.state.store.get_job(str(job_id))
        if result is None:
            raise HTTPException(404, "Unknown job")
        return result

    return app
