"""Deterministic drift indicators and explicit retraining gates."""

import numpy as np
import pandas as pd
from bank_marketing.modeling.core import metrics


def psi(reference, current):
    """Population stability index; reference-only bins, missing values kept separately."""
    ref, cur = pd.Series(reference), pd.Series(current)
    if pd.api.types.is_numeric_dtype(ref):
        edges = np.unique(np.quantile(ref.dropna(), np.linspace(0, 1, 11)))
        edges = np.unique(np.r_[-np.inf, edges[1:-1], np.inf])
        a = pd.cut(ref, edges).value_counts(sort=False, dropna=False)
        b = pd.cut(cur, edges).value_counts(sort=False, dropna=False)
    else:
        a = ref.fillna("__missing__").astype(str).value_counts()
        b = cur.fillna("__missing__").astype(str).value_counts()
    keys = a.index.union(b.index)
    pa = a.reindex(keys, fill_value=0).to_numpy(dtype=float) + 0.5
    pb = b.reindex(keys, fill_value=0).to_numpy(dtype=float) + 0.5
    pa /= pa.sum()
    pb /= pb.sum()
    return float(np.sum((pb - pa) * np.log(pb / pa)))


def drift_report(reference, current, features):
    return [
        {
            "feature": c,
            "psi": psi(reference[c], current[c]),
            "alert": psi(reference[c], current[c]) > 0.2,
        }
        for c in features
    ]


def retraining_decision(y, probabilities, reference_ap, drift_alert=False, min_labels=200):
    """Alert requests investigation/retraining; never promotes a model."""
    y = np.asarray(y, dtype=int)
    if len(y) < min_labels or len(np.unique(y)) < 2:
        return dict(
            retrain=False,
            reason="insufficient_labels",
            n_labels=len(y),
            investigate_drift=bool(drift_alert),
            automatic_promotion=False,
        )
    result = metrics(y, probabilities)
    degraded = result["average_precision"] < reference_ap - 0.05
    return dict(
        retrain=bool(degraded),
        reason="ap_drop" if degraded else "stable",
        n_labels=len(y),
        average_precision=result["average_precision"],
        brier=result["brier"],
        investigate_drift=bool(drift_alert),
        automatic_promotion=False,
    )
