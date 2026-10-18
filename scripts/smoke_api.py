"""Verify real artifact through ASGI, export OpenAPI and measured local latency."""

import json
import time
from pathlib import Path
import numpy as np
from fastapi.testclient import TestClient
from loguru import logger
from bank_marketing.service.app import create_app

logger.remove()
with TestClient(create_app(db_path="runtime/smoke.sqlite", api_key="smoke-only")) as client:
    client.headers["Authorization"] = "Bearer smoke-only"
    payload = json.loads(Path("reports/example_request.json").read_text())
    assert client.get("/health").status_code == 200
    response = client.post("/predict", json=payload)
    assert response.status_code == 200, response.text
    Path("reports/api_example_response.json").write_text(
        json.dumps(response.json(), indent=2) + "\n"
    )
    request_id = response.json()["request_id"]
    assert (
        client.post("/feedback", json={"request_id": request_id, "outcome": "no"}).status_code
        == 200
    )
    # This is explicitly synthetic smoke feedback in an isolated database.
    durations = []
    for _ in range(100):
        start = time.perf_counter()
        r = client.post("/predict", json=payload)
        assert r.status_code == 200
        durations.append((time.perf_counter() - start) * 1000)
    evidence = dict(
        requests=100,
        p50_ms=float(np.percentile(durations, 50)),
        p95_ms=float(np.percentile(durations, 95)),
        errors=0,
        method="In-process ASGI TestClient, sequential, not network/load performance",
        synthetic_feedback=True,
    )
    Path("reports/api_smoke.json").write_text(json.dumps(evidence, indent=2) + "\n")
    Path("reports/openapi.json").write_text(
        json.dumps(client.get("/openapi.json").json(), indent=2) + "\n"
    )
    print(json.dumps(evidence, indent=2))
