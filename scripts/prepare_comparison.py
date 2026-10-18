"""Fetch allowlisted files from a hash-verified champion ZIP and approved evaluation CSV."""

import hashlib
import io
import os
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile


def fetch(prefix):
    url = os.environ[prefix + "_URL"]
    expected = os.environ[prefix + "_SHA256"]
    assert url.startswith("https://") and len(expected) == 64
    with urlopen(url, timeout=60) as response:
        data = response.read()
    assert hashlib.sha256(data).hexdigest() == expected, "Approved snapshot hash mismatch"
    return data


champion = fetch("CHAMPION")
evaluation = fetch("EVALUATION")
root = Path("runtime/comparison")
root.mkdir(parents=True, exist_ok=True)
folder = root / "champion"
folder.mkdir(exist_ok=True)
archive = ZipFile(io.BytesIO(champion))
for required in ["model.joblib", "model.sha256", "training_reference.csv"]:
    matches = [n for n in archive.namelist() if n.split("/")[-1] == required]
    assert len(matches) == 1, f"Expected exactly one {required}"
    (folder / required).write_bytes(archive.read(matches[0]))
(root / "evaluation.csv").write_bytes(evaluation)
