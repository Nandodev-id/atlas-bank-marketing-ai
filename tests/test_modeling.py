import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from bank_marketing.modeling.core import FeatureBuilder, make_pipeline, metrics, scenarios
from bank_marketing.modeling.train import clean_later
from bank_marketing.monitoring.checks import psi, retraining_decision


def test_feature_scenarios_exclude_leakage_and_sensitive_columns():
    columns = [
        "age",
        "job",
        "duration",
        "pdays",
        "campaign",
        "contact",
        "default",
        "euribor3m",
        "y",
    ]
    s = scenarios(columns)
    assert "duration" in s["S1"] and "duration" not in s["S2"]
    assert not {"age", "job", "duration"} & set(s["S3"])
    assert s["S4"] == ["default", "euribor3m"]


def test_sentinel_is_not_scaled_as_real_elapsed_time():
    source = pd.DataFrame({"pdays": [999, 5]})
    out = FeatureBuilder().fit_transform(source)
    assert np.isnan(out.pdays.iloc[0]) and out.previously_contacted.tolist() == [0, 1]
    assert source.pdays.iloc[0] == 999


def test_preprocessing_does_not_learn_validation_category_or_median():
    train = pd.DataFrame({"pdays": [999, 2, 4, 999], "default": ["no"] * 4})
    pipe = make_pipeline(list(train), LogisticRegression()).fit(train, [0, 1, 0, 1])
    imputer = pipe["prep"].named_transformers_["num"]["imputer"]
    assert imputer.statistics_[0] == 3
    result = pipe.predict_proba(pd.DataFrame({"pdays": [800], "default": ["unknown"]}))
    assert result.shape == (1, 2)
    assert pipe["prep"].named_transformers_["cat"]["onehot"].categories_[0].tolist() == ["no"]
    assert imputer.statistics_[0] == 3


def test_feature_duplicate_purge_does_not_depend_on_label():
    earlier = pd.DataFrame({"x": [1], "y": ["no"]})
    later = pd.DataFrame({"x": [1, 2], "y": ["yes", "no"]})
    assert clean_later(earlier, later).x.tolist() == [2]


def test_majority_accuracy_is_not_positive_recall():
    m = metrics([0] * 9 + [1], [0.1] * 10)
    assert m["accuracy"] == 0.9 and m["recall"] == 0 and m["roc_auc"] == 0.5


def test_psi_detects_changed_distribution():
    ref = pd.Series(np.arange(1000))
    assert psi(ref, ref) == 0
    assert psi(ref, ref + 10000) > 0.2
    assert psi(pd.Series(["a"] * 100), pd.Series(["b"] * 100)) > 0.2


def test_retraining_requires_labels_and_never_promotes():
    assert retraining_decision([1, 0], [0.1, 0.9], 0.8)["reason"] == "insufficient_labels"
    result = retraining_decision([0, 1] * 150, [0.9, 0.1] * 150, 0.8)
    assert result["retrain"] and not result["automatic_promotion"]


def test_fairness_gate_does_not_treat_insufficient_groups_as_zero_gap():
    from bank_marketing.modeling.core import fairness_gaps

    table = pd.DataFrame(
        {
            "attribute": ["age_band", "age_band"],
            "small_sample": [False, True],
            "fpr": [0.1, 0.1],
            "fnr": [0.2, 0.2],
            "selection_rate": [0.3, 0.3],
        }
    )
    assert fairness_gaps(table)["fpr"] is None
