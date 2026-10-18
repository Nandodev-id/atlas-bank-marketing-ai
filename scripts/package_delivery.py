"""Package source, executed evidence, trusted artifacts and licensed exam data.
Never include credentials, Git history, Python environments or live audit databases.
"""

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
excluded = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    ".cache",
    "runtime",
    "__pycache__",
    ".ipynb_checkpoints",
    ".DS_Store",
    ".trash",
    "build",
    "dist",
}
files = []
for path in root.rglob("*"):
    rel = path.relative_to(root)
    if not path.is_file() or any(
        part in excluded or part.endswith(".egg-info") for part in rel.parts
    ):
        continue
    if path.name.startswith(".env") and path.name != ".env.example":
        continue
    if path.suffix in [".pyc", ".zip", ".sqlite", ".db"]:
        continue
    if rel.as_posix() == "reports/delivery_manifest.json":
        continue
    files.append(path)
manifest = {
    str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)
}
manifest_path = root / "reports/delivery_manifest.json"
manifest_path.write_text(
    json.dumps({"hash_algorithm": "sha256", "files": manifest}, indent=2) + "\n"
)
files.append(manifest_path)
archive = root.parent / "atlas-bank-marketing-ai-delivery.zip"
with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=6) as package:
    for path in sorted(files):
        package.write(path, Path(root.name) / path.relative_to(root))
with ZipFile(archive) as package:
    assert package.testzip() is None
    for name, digest in manifest.items():
        assert hashlib.sha256(package.read(f"{root.name}/{name}")).hexdigest() == digest
    names = package.namelist()
    assert not any("/.venv/" in n or "/runtime/" in n or n.endswith("/.env") for n in names)
print(
    json.dumps(
        {
            "archive": str(archive),
            "files": len(files),
            "bytes": archive.stat().st_size,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        },
        indent=2,
    )
)
