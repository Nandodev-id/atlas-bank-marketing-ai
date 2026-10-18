"""Run Streamlit interactions against the real model via an in-process API bridge."""

import json
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from loguru import logger
from streamlit.testing.v1 import AppTest
from bank_marketing.service.app import create_app

logger.remove()
with TestClient(create_app(db_path="runtime/ui-smoke.sqlite", api_key="")) as client:

    def request(method, url, headers=None, timeout=None, **kwargs):
        path = "/" + url.split("/", 3)[3]
        return client.request(method, path, headers=headers, **kwargs)

    with patch("requests.request", side_effect=request):
        app = AppTest.from_file("ui/app.py", default_timeout=30).run()
        assert not app.exception
        print("Buttons:", [(b.label, b.key) for b in app.button])
        next(b for b in app.button if b.label == "Estimer la souscription").click().run()
        assert not app.exception
        assert "prediction" in app.session_state
        next(b for b in app.button if b.label == "Enregistrer le retour observé").click().run()
        assert not app.exception
        next(b for b in app.button if b.label == "Actualiser les indicateurs").click().run()
        assert not app.exception
        evidence = dict(
            status="passed",
            tabs=[t.label for t in app.tabs],
            interactions=["form render", "prediction", "feedback", "monitoring refresh"],
            method="Streamlit AppTest plus real FastAPI TestClient bridge; no browser/socket",
            synthetic_feedback=True,
        )
        Path("reports/ui_smoke.json").write_text(json.dumps(evidence, indent=2) + "\n")
        print(json.dumps(evidence, indent=2))
