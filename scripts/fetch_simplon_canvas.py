"""Fetch a read-only reference copy of the canonical Simplon certification canvas.

Run only on a machine with network access. Never overwrite our working notebook.
"""

import json
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URL = (
    "https://raw.githubusercontent.com/Formation-SIMPLON-IA/"
    "ia-dev-id-ressources/main/cas_usage_certif/canvas-cas-usage-v2.ipynb"
)
DESTINATION = Path(__file__).resolve().parents[1] / "cas_usage_certif/canvas-cas-usage-v2.ipynb"


def main() -> None:
    request = Request(SOURCE_URL, headers={"User-Agent": "AtlasCertificationStarter/1.0"})
    with urlopen(request, timeout=20) as response:
        contents = response.read()
    notebook = json.loads(contents)
    if not isinstance(notebook, dict) or "cells" not in notebook or "nbformat" not in notebook:
        raise ValueError("Remote content is not a Jupyter notebook")
    if DESTINATION.exists():
        raise FileExistsError(f"Reference already exists: {DESTINATION}")
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_bytes(contents)
    print(f"Downloaded official Simplon reference: {DESTINATION}")


if __name__ == "__main__":
    main()
