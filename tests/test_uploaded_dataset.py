"""Optional integration test; skipped in CI because the public raw CSV is not committed."""

from pathlib import Path

import pytest

from bank_marketing.data.inspection import inspect_csv


DATASET = Path(__file__).resolve().parents[1] / "data/raw/bank-additional-full.csv"


@pytest.mark.skipif(not DATASET.exists(), reason="Full raw CSV intentionally excluded from Git")
def test_original_dataset_snapshot() -> None:
    result = inspect_csv(DATASET)
    assert result.row_count == 41_188
    assert result.target_counts == {"no": 36_548, "yes": 4_640}
    assert result.duplicate_row_count == 12
    assert result.pdays_999_count == 39_673
    assert result.sha256 == "74adfc578bf77a7ff4bb1ba4a9f8709d9e3c6907342959c2c8416847e0afb4d8"
