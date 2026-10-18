"""Record the actually used environment without embedding local credentials or URLs."""

import importlib.metadata as m
import json
import platform
from pathlib import Path

packages = [
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "joblib",
    "matplotlib",
    "seaborn",
    "fastapi",
    "pydantic",
    "uvicorn",
    "httpx",
    "loguru",
    "prometheus-client",
    "mlflow",
    "streamlit",
    "requests",
    "pytest",
    "nbformat",
    "nbclient",
    "nbconvert",
    "ipykernel",
]
versions = {p: m.version(p) for p in packages}
Path("requirements-runtime.txt").write_text(
    "\n".join(
        f"{p}=={v}"
        for p, v in versions.items()
        if p not in ["pytest", "nbformat", "nbclient", "nbconvert", "ipykernel"]
    )
    + "\n"
)
Path("requirements-tested.txt").write_text(
    "\n".join(f"{p}=={v}" for p, v in versions.items()) + "\n"
)
Path("reports/environment.json").write_text(
    json.dumps(
        {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": versions,
            "note": "Direct dependencies pinned; transitive versions are recorded separately.",
        },
        indent=2,
    )
    + "\n"
)
all_versions = sorted(
    {(d.metadata["Name"], d.version) for d in m.distributions() if d.metadata["Name"]}
)
Path("reports/environment_all_packages.json").write_text(
    json.dumps(dict(all_versions), indent=2) + "\n"
)
