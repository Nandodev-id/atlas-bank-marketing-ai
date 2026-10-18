"""Fast, dataset-independent tests suitable for GitHub Actions."""

import csv
from pathlib import Path

import pytest

from bank_marketing.data.inspection import inspect_csv
from bank_marketing.data.schema import EXPECTED_COLUMNS


def write_csv(path: Path, *, target: str = "yes", bad_header: bool = False) -> None:
    columns = list(EXPECTED_COLUMNS)
    if bad_header:
        columns[-1] = "outcome"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, delimiter=";")
        writer.writeheader()
        row = {col: "0" for col in columns}
        row["pdays"] = "999"
        row[columns[-1]] = target
        writer.writerow(row)
        writer.writerow(row)  # Intentional exact duplicate.


def test_inspection_records_statistics(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    write_csv(path)
    summary = inspect_csv(path)
    assert summary.row_count == 2
    assert summary.column_count == 21
    assert summary.target_counts == {"yes": 2}
    assert summary.duplicate_row_count == 1
    assert summary.pdays_999_count == 2
    assert len(summary.sha256) == 64


def test_rejects_unexpected_header(tmp_path: Path) -> None:
    path = tmp_path / "unexpected.csv"
    write_csv(path, bad_header=True)
    with pytest.raises(ValueError, match="columns"):
        inspect_csv(path)


def test_rejects_unknown_target(tmp_path: Path) -> None:
    path = tmp_path / "bad-target.csv"
    write_csv(path, target="maybe")
    with pytest.raises(ValueError, match="target"):
        inspect_csv(path)


def test_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        inspect_csv(Path("does-not-exist.csv"))
