"""Download the exact public UCI source and verify before writing it."""

import hashlib
import io
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

root = Path(__file__).resolve().parents[1]
expected = (root / "data/raw/DATASET.sha256").read_text().split()[0]
with urlopen(
    "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip", timeout=60
) as response:
    outer = ZipFile(io.BytesIO(response.read()))
    names = outer.namelist()
    if "bank-additional.zip" in names:
        archive = ZipFile(io.BytesIO(outer.read("bank-additional.zip")))
    else:
        archive = outer
    name = next(n for n in archive.namelist() if n.endswith("bank-additional-full.csv"))
    contents = archive.read(name)
assert (
    hashlib.sha256(contents).hexdigest() == expected
), "Source hash mismatch: investigate; do not silently accept"
path = root / "data/raw/bank-additional-full.csv"
path.parent.mkdir(parents=True, exist_ok=True)
if path.exists() and path.read_bytes() != contents:
    raise SystemExit("Existing dataset differs")
path.write_bytes(contents)
print("Verified UCI snapshot:", path)
