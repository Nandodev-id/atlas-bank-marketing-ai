"""Read-only source-file inspection, used to establish a reproducible baseline."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from bank_marketing.data.schema import CSV_DELIMITER, EXPECTED_COLUMNS, TARGET_VALUES


@dataclass(frozen=True)
class DatasetSummary:
    row_count: int
    column_count: int
    target_counts: dict[str, int]
    duplicate_row_count: int
    pdays_999_count: int
    unknown_counts: dict[str, int]
    sha256: str


def inspect_csv(path: Path) -> DatasetSummary:
    """Validate the exact source header and count data-quality signals, without changes."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV missing: {path}")

    target_counts: Counter[str] = Counter()
    unknown_counts: Counter[str] = Counter()
    seen_rows: set[tuple[str, ...]] = set()
    duplicates = 0
    never_contacted = 0
    rows = 0

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=CSV_DELIMITER, strict=True)
        if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
            raise ValueError("CSV columns differ from the documented 21-column schema")

        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV at line {row_number}")
            label = row["y"]
            if label not in TARGET_VALUES:
                raise ValueError(f"Unknown target value {label!r} at line {row_number}")
            rows += 1
            target_counts[label] += 1
            if row["pdays"] == "999":
                never_contacted += 1
            for column, value in row.items():
                if value == "unknown":
                    unknown_counts[column] += 1
            signature = tuple(row[column] for column in EXPECTED_COLUMNS)
            if signature in seen_rows:
                duplicates += 1
            else:
                seen_rows.add(signature)

    with path.open("rb") as file:
        sha256 = hashlib.file_digest(file, "sha256").hexdigest()
    return DatasetSummary(
        row_count=rows,
        column_count=len(EXPECTED_COLUMNS),
        target_counts=dict(sorted(target_counts.items())),
        duplicate_row_count=duplicates,
        pdays_999_count=never_contacted,
        unknown_counts=dict(sorted(unknown_counts.items())),
        sha256=sha256,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and summarize the raw banking CSV")
    parser.add_argument("--dataset", type=Path, default=Path("data/raw/bank-additional-full.csv"))
    parser.add_argument("--manifest", type=Path, default=Path("data/raw/DATASET.sha256"))
    args = parser.parse_args()
    result = inspect_csv(args.dataset)
    if args.manifest.is_file():
        expected = args.manifest.read_text(encoding="utf-8").split()[0]
        if expected != result.sha256:
            parser.error("Dataset SHA-256 differs from the expected source snapshot")
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
