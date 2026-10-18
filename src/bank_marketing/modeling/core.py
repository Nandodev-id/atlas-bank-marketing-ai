"""Shared, serializable preprocessing and metrics; no fitted global objects."""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

SENSITIVE = ["age", "job", "marital", "education"]
HISTORY = ["campaign", "pdays", "previous", "poutcome"]
NUMERIC = [
    "age",
    "duration",
    "campaign",
    "pdays",
    "previous",
    "emp.var.rate",
    "cons.price.idx",
    "cons.conf.idx",
    "euribor3m",
    "nr.employed",
]


def scenarios(columns):
    all_features = [x for x in columns if x != "y"]
    return {
        "S1": all_features,
        "S2": [x for x in all_features if x != "duration"],
        "S3": [x for x in all_features if x not in ["duration", *SENSITIVE]],
        "S4": [
            x
            for x in all_features
            if x not in ["duration", *SENSITIVE, *HISTORY, "contact", "month", "day_of_week"]
        ],
    }


class FeatureBuilder(BaseEstimator, TransformerMixin):
    """Deterministic features, reused identically in every fold and at inference."""

    def fit(self, X, y=None):
        self.feature_names_in_ = np.array(X.columns, dtype=object)
        return self

    def transform(self, X):
        out = X.copy()
        if "pdays" in out:
            out["previously_contacted"] = (out["pdays"] != 999).astype(float)
            out["pdays"] = out["pdays"].replace(999, np.nan)
        return out


def make_pipeline(features, estimator):
    num = [c for c in features if c in NUMERIC]
    if "pdays" in features:
        num.append("previously_contacted")
    cat = [c for c in features if c not in NUMERIC]
    transforms = []
    if num:
        transforms.append(
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                        ("scaler", StandardScaler()),
                    ]
                ),
                num,
            )
        )
    if cat:
        transforms.append(
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                cat,
            )
        )
    return Pipeline(
        [
            ("features", FeatureBuilder()),
            ("prep", ColumnTransformer(transforms)),
            ("model", clone(estimator)),
        ]
    )


def metrics(y, p, threshold=0.5):
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    # Seeded tie breaking avoids advantaging early/late rows when scores are tied.
    rng = np.random.default_rng(42)
    order = np.lexsort((rng.random(len(p)), -p))
    k = max(1, int(np.ceil(len(p) * 0.2)))
    precision20 = float(y[order[:k]].mean())
    return dict(
        n=len(y),
        prevalence=float(y.mean()),
        accuracy=float(accuracy_score(y, pred)),
        precision=float(precision_score(y, pred, zero_division=0)),
        recall=float(recall_score(y, pred, zero_division=0)),
        f1=float(f1_score(y, pred, zero_division=0)),
        roc_auc=float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
        average_precision=float(average_precision_score(y, p)) if y.sum() else None,
        brier=float(brier_score_loss(y, p)),
        precision_at_20=precision20,
        lift_at_20=precision20 / float(y.mean()) if y.sum() else None,
        selection_rate=float(pred.mean()),
        tn=int(tn),
        fp=int(fp),
        fn=int(fn),
        tp=int(tp),
    )


def logit(p):
    p = np.clip(np.asarray(p), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p)).reshape(-1, 1)


def predict_bundle(bundle, frame):
    p = bundle["pipeline"].predict_proba(frame[bundle["features"]])[:, 1]
    if bundle.get("calibrator") is not None:
        p = bundle["calibrator"].predict_proba(logit(p))[:, 1]
    return p


def subgroup_metrics(frame, y, p, threshold):
    groups = {
        "age_band": pd.cut(
            frame.age, [0, 30, 45, 60, 120], labels=["<=30", "31-45", "46-60", ">60"]
        ),
        "job": frame.job,
        "marital": frame.marital,
        "education": frame.education,
    }
    rows = []
    y, p = np.asarray(y), np.asarray(p)
    for attribute, values in groups.items():
        for group in sorted(values.dropna().unique()):
            mask = np.asarray(values == group)
            m = metrics(y[mask], p[mask], threshold)
            m.update(
                attribute=attribute,
                group=str(group),
                fpr=m["fp"] / (m["fp"] + m["tn"]) if m["fp"] + m["tn"] else None,
                fnr=m["fn"] / (m["fn"] + m["tp"]) if m["fn"] + m["tp"] else None,
                small_sample=m["n"] < 100 or min(m["tp"] + m["fn"], m["tn"] + m["fp"]) < 20,
            )
            rows.append(m)
    return pd.DataFrame(rows)


def fairness_gaps(table):
    """Return no estimate when any audited attribute lacks two reliable groups."""
    valid = table[~table.small_sample]
    group_counts = valid.groupby("attribute").size()
    enough = all(group_counts.get(attribute, 0) >= 2 for attribute in table.attribute.unique())
    if not enough:
        return {key: None for key in ["fpr", "fnr", "selection_rate"]}
    return {
        key: float(valid.groupby("attribute")[key].agg(lambda s: s.max() - s.min()).max())
        for key in ["fpr", "fnr", "selection_rate"]
    }
