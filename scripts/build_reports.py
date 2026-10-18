"""Build figures from the frozen experiment; never retrain or tune on test."""

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/atlas-mpl")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib
from sklearn.calibration import calibration_curve
from sklearn.metrics import ConfusionMatrixDisplay, PrecisionRecallDisplay, RocCurveDisplay
from bank_marketing.modeling.core import metrics
from bank_marketing.monitoring.checks import drift_report
from bank_marketing.service.app import ood_reasons

root = Path(__file__).resolve().parents[1]
os.chdir(root)
out = root / "reports"
fig = out / "figures"
fig.mkdir(exist_ok=True)
plt.rcParams.update(
    {
        "figure.dpi": 130,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
        "axes.titlesize": 13,
        "figure.facecolor": "white",
    }
)
data = pd.read_csv("data/raw/bank-additional-full.csv", sep=";")
splits = json.loads(Path("artifacts/split_indices.json").read_text())
train = data.loc[splits["train"]].copy()
selection = json.loads((out / "selection.json").read_text())
final = json.loads((out / "final_test.json").read_text())
cv = pd.read_csv(out / "cv_comparison.csv")
bundle = joblib.load("artifacts/model.joblib")


def save(name):
    plt.tight_layout()
    plt.savefig(fig / name, bbox_inches="tight")
    plt.close()


audit = {
    "source_rows": len(data),
    "source_columns": len(data.columns),
    "source_duplicates": int(data.duplicated().sum()),
    "train_rows": len(train),
    "train_nulls": train.isna().sum().to_dict(),
    "train_unknown": {
        c: int((train[c] == "unknown").sum())
        for c in train.select_dtypes("object")
        if (train[c] == "unknown").any()
    },
    "train_pdays_999": int((train.pdays == 999).sum()),
    "train_duplicates": int(train.duplicated().sum()),
    "split_sizes": {k: len(v) for k, v in splits.items()},
    "split_prevalence": {k: float((data.loc[v, "y"] == "yes").mean()) for k, v in splits.items()},
}
(out / "data_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
train.describe(include="all").T.to_csv(out / "train_describe.csv")
train.isna().sum().rename("null_count").to_csv(out / "train_missing.csv")

plt.figure(figsize=(6, 3))
counts = train.y.value_counts().reindex(["no", "yes"])
plt.bar(["Non", "Oui"], counts, color=["#497485", "#d48445"])
plt.title("Cible — entraînement uniquement")
plt.ylabel("Observations")
save("target.png")
plt.figure(figsize=(8, 3))
plt.bar(
    audit["split_prevalence"].keys(),
    np.array(list(audit["split_prevalence"].values())) * 100,
    color="#497485",
)
plt.ylabel("Souscriptions (%)")
plt.title("Dérive temporelle constatée après ouverture du test")
save("time_shift.png")
plt.figure(figsize=(8, 3))
plt.barh(list(audit["train_unknown"]), list(audit["train_unknown"].values()), color="#d48445")
plt.title("Valeurs « unknown » — entraînement")
save("unknown.png")
train[["age", "campaign", "duration", "euribor3m"]].hist(figsize=(9, 6), bins=35, color="#497485")
plt.suptitle("Distributions — entraînement")
save("distributions.png")
corr = train.select_dtypes("number").corr()
corr.to_csv(out / "train_correlations.csv")
plt.figure(figsize=(9, 7))
plt.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
plt.xticks(range(len(corr)), corr.columns, rotation=80)
plt.yticks(range(len(corr)), corr.columns)
plt.colorbar(label="Corrélation")
plt.title("Corrélations numériques — entraînement")
save("correlations.png")
pivot = cv.pivot(index="scenario", columns="model", values="average_precision")
pivot.plot.bar(figsize=(10, 4))
plt.ylabel("Average precision moyenne")
plt.title("Même protocole : scénarios × modèles — CV temporelle")
plt.legend(fontsize=8)
save("cv_scenarios.png")
pred = pd.read_csv("artifacts/test_predictions.csv")
yt = pred.y
pt = pred.probability
ConfusionMatrixDisplay.from_predictions(
    yt, pt >= selection["threshold"], display_labels=["Non", "Oui"], cmap="Blues", colorbar=False
)
plt.title("Test final — seuil fixé sur validation")
save("confusion.png")
fig2, axes = plt.subplots(1, 2, figsize=(10, 4))
PrecisionRecallDisplay.from_predictions(yt, pt, ax=axes[0])
axes[0].axhline(yt.mean(), ls="--", color="gray", label="Prévalence")
axes[0].legend()
RocCurveDisplay.from_predictions(yt, pt, ax=axes[1])
axes[1].plot([0, 1], [0, 1], "--", color="gray")
plt.suptitle("Test final — qualité du classement")
save("curves.png")
prob_true, prob_pred = calibration_curve(yt, pt, n_bins=8, strategy="quantile")
plt.figure(figsize=(5, 4))
plt.plot([0, 1], [0, 1], "--", color="gray")
plt.plot(prob_pred, prob_true, "o-", color="#497485")
plt.xlabel("Probabilité annoncée")
plt.ylabel("Fréquence observée")
plt.title("Calibration — test final")
save("calibration.png")
imp = pd.read_csv(out / "permutation_importance.csv").sort_values("importance")
plt.figure(figsize=(8, 4))
plt.barh(imp.feature, imp.importance, xerr=imp["std"], color="#497485")
plt.xlabel("Baisse d’AP après permutation")
plt.title("Importance sur validation — corrélations à considérer")
save("importance.png")
fair = pd.read_csv(out / "fairness_test.csv")
age = fair[fair.attribute == "age_band"].set_index("group")
age[["selection_rate", "fpr", "fnr"]].plot.bar(figsize=(8, 4))
plt.ylim(0, 1)
plt.title("Équité — résultats descriptifs par tranche d’âge")
plt.legend(["Sélection", "Faux positifs", "Faux négatifs"])
save("fairness_age.png")
current = data.loc[splits["test"]]
drift = drift_report(train, current, bundle["features"])
pd.DataFrame(drift).to_csv(out / "drift_test.csv", index=False)
reasons = [ood_reasons(row, bundle) for row in current[bundle["features"]].to_dict("records")]
ood = np.array([bool(r) for r in reasons])
near = abs(pt.to_numpy() - bundle["threshold"]) <= bundle["abstention_margin"]
accepted = ~ood & ~near
fallback = dict(
    n=len(current),
    ood_count=int(ood.sum()),
    near_threshold_count=int((near & ~ood).sum()),
    coverage=float(accepted.mean()),
    accepted_metrics=(
        metrics(yt[accepted], pt[accepted], bundle["threshold"]) if accepted.any() else None
    ),
    note="Offline selective-service simulation; full-test model scores above do not include this abstention policy.",
)
(out / "fallback_test.json").write_text(json.dumps(fallback, indent=2) + "\n")
# Leakage delta matched by model, never mixing model and feature effects.
delta = cv.pivot(index="model", columns="scenario", values="average_precision")
delta["S1_minus_S2"] = delta.S1 - delta.S2
delta.to_csv(out / "scenario_deltas.csv")
print(
    json.dumps(
        {
            "audit": audit,
            "fallback": fallback,
            "fairness_age": age[["n", "fpr", "fnr", "selection_rate"]].to_dict(),
        },
        indent=2,
    )
)
