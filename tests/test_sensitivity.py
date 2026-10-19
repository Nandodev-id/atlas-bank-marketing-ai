import pandas as pd
import pytest

from bank_marketing.modeling.sensitivity import load_development


def test_held_out_values_cannot_change_development(tmp_path):
    path = tmp_path / 'data.csv'
    splits = {'train': [0, 1], 'calibration': [2], 'validation': [3], 'test': [4, 5]}
    prefix = 'age;default;y\n20;no;no\n30;no;yes\n40;unknown;no\n50;yes;yes\n'
    path.write_text(prefix + '60;no;no\n70;unknown;yes\n')
    before, duplicates = load_development(path, splits)
    # Even malformed held-out records must not be parsed by this analysis.
    path.write_text(prefix + 'not;a;valid;test;row\nother;invalid;record;extra\n')
    after, _ = load_development(path, splits)
    pd.testing.assert_frame_equal(before, after)
    assert duplicates == 0 and list(after.index) == [0, 1, 2, 3]


@pytest.mark.parametrize('test', [[2, 4], [0, 5]])
def test_overlap_is_rejected_before_csv_read(tmp_path, test):
    with pytest.raises(ValueError, match='overlap'):
        load_development(tmp_path / 'missing.csv',
                         {'train': [0, 1], 'calibration': [2], 'validation': [3], 'test': test})


def test_identical_predictor_profiles_do_not_cross_folds(tmp_path):
    path = tmp_path / 'data.csv'
    path.write_text('age;default;y\n20;no;no\n30;no;yes\n20;no;yes\n40;no;no\n50;yes;yes\n')
    frame, removed = load_development(path, {'train': [0, 1], 'calibration': [2],
                                           'validation': [3], 'test': [4]})
    assert removed == 1 and list(frame.index) == [0, 1, 3]
