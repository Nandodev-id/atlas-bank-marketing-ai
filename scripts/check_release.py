"""Machine gate for a candidate; human production approval remains separate."""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--reports", default="reports")
parser.add_argument("--production", action="store_true")
args = parser.parse_args()
root = Path(args.reports)
test = json.loads((root / "final_test.json").read_text())
selection = json.loads((root / "selection.json").read_text())
if selection["scenario"] == "S1" or "duration" in selection["features"]:
    raise SystemExit("Blocked: leakage scenario cannot be promoted.")
if not test["local_gate_passed"]:
    raise SystemExit("Blocked: local statistical/latency gates failed.")
if args.production:
    decision = json.loads((root / "production_decision.json").read_text())
    if not decision["production_gate_passed"]:
        raise SystemExit("Blocked by production review: " + str(decision["checks"]))
print("Local candidate gate passed. Production requires recent-data, fairness and human approval.")
