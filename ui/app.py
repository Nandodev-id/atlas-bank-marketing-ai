"""Run: streamlit run ui/app.py. Communicates with the API; never loads a model."""

import json
import os
from pathlib import Path
import pandas as pd
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
st.set_page_config(page_title="Atlas | Marketing responsable", page_icon="🏦", layout="wide")
st.title("Atlas — Marketing bancaire responsable")
st.caption(
    "Démonstration pédagogique · Aide à la décision · Aucune autorisation automatique de contact"
)
api = os.getenv("ATLAS_API_URL", "http://127.0.0.1:8000").rstrip("/")
key = os.getenv("ATLAS_API_KEY", "")
headers = {"Authorization": "Bearer " + key} if key else {}


def call(method, path, **kwargs):
    response = requests.request(method, api + path, headers=headers, timeout=15, **kwargs)
    response.raise_for_status()
    return response.json()


FIELD_LABELS = {
    "default": "Crédit en défaut de paiement (default)",
    "housing": "Prêt immobilier en cours (housing)",
    "loan": "Prêt personnel en cours (loan)",
    "emp.var.rate": "Variation de l’emploi (emp.var.rate)",
    "cons.price.idx": "Indice des prix à la consommation (cons.price.idx)",
    "cons.conf.idx": "Indice de confiance des consommateurs (cons.conf.idx)",
    "euribor3m": "Taux Euribor à 3 mois (euribor3m)",
    "nr.employed": "Indicateur du nombre de salariés (nr.employed)",
}
CHOICE_LABELS = {"no": "Non", "yes": "Oui", "unknown": "Information inconnue"}
FIELD_HELP = {
    "default": "Le client a-t-il un crédit en défaut de paiement ? Ce champ ne décrit pas la souscription. Information inconnue ne signifie pas Non.",
    "housing": "Le client a-t-il un prêt immobilier ?",
    "loan": "Le client a-t-il un prêt personnel ?",
}


prediction, results, monitoring = st.tabs(
    ["Simuler un profil", "Résultats de l’étude", "Suivi du service"]
)
with prediction:
    st.info(
        "Ce modèle historique est un candidat de démonstration. Le contrôle temporel et les écarts entre groupes empêchent une mise en production."
    )
    try:
        model = call("GET", "/model")
        st.caption(f"Version {model['version']} · {model['scenario']} · {model['model']}")
        with st.form("profile"):
            values = {}
            cols = st.columns(2)
            for i, feature in enumerate(model["features"]):
                ref = model["reference"][feature]
                with cols[i % 2]:
                    if ref["kind"] == "categorical":
                        values[feature] = st.selectbox(
                            FIELD_LABELS.get(feature, feature),
                            ref["categories"],
                            format_func=lambda value: CHOICE_LABELS.get(value, value),
                            help=FIELD_HELP.get(feature),
                            key="feature_" + feature,
                        )
                    else:
                        values[feature] = st.number_input(
                            FIELD_LABELS.get(feature, feature),
                            value=float(ref["median"]),
                            format="%.3f",
                        )
            st.caption(
                "Les plages historiques sont contrôlées par le service. Un profil inhabituel est transmis à un humain."
            )
            submitted = st.form_submit_button("Estimer la souscription")
        if submitted:
            st.session_state["prediction"] = call("POST", "/predict", json={"features": values})
        if "prediction" in st.session_state:
            result = st.session_state["prediction"]
            if result["abstain"]:
                st.warning("Révision humaine nécessaire : " + ", ".join(result["reasons"]))
            elif result["probability"] is not None:
                st.metric("Probabilité estimée", f"{result['probability']:.1%}")
                st.write("Priorité indicative : " + result["prediction"])
            st.caption(
                "Le consentement ou une exception légalement applicable doit être contrôlé séparément dans le SI métier."
            )
            with st.expander("Réponse traçable"):
                st.json(result)
            with st.form("feedback"):
                outcome = st.selectbox(
                    "Souscription réellement observée après suivi", ["no", "yes"]
                )
                if st.form_submit_button("Enregistrer le retour observé"):
                    call(
                        "POST",
                        "/feedback",
                        json={"request_id": result["request_id"], "outcome": outcome},
                    )
                    st.success(
                        "Retour enregistré. Aucun réentraînement ou déploiement automatique."
                    )
    except (requests.RequestException, KeyError) as exc:
        st.warning("API indisponible. Démarrer le service avec : python -m bank_marketing.service")
with results:
    if (ROOT / "reports/final_test.json").exists():
        report = json.loads((ROOT / "reports/final_test.json").read_text())
        cols = st.columns(3)
        cols[0].metric("ROC-AUC historique", f"{report['roc_auc']:.3f}")
        cols[1].metric("Average precision", f"{report['average_precision']:.3f}")
        cols[2].metric("Lift des 20 % prioritaires", f"{report['lift_at_20']:.2f}×")
        st.error(
            "Décision : ne pas déployer. La politique de sécurité s’abstient sur 100 % du bloc temporel final ; les scores ci-dessus évaluent le modèle sans ce filtre."
        )
        st.dataframe(pd.read_csv(ROOT / "reports/cv_comparison.csv"), use_container_width=True)
        st.image(str(ROOT / "reports/figures/time_shift.png"))
        st.image(str(ROOT / "reports/figures/fairness_age.png"))
    else:
        st.info("Exécuter les expériences pour produire les résultats.")
with monitoring:
    if st.button("Actualiser les indicateurs"):
        try:
            status = call("GET", "/monitoring")
            st.metric("Prédictions enregistrées", status["requests"])
            st.metric("Retours exploitables", status["labeled"])
            st.write("Taux d’abstention", status["abstention_rate"])
            st.write("Réentraînement", status["retraining"])
            if status["drift"]:
                st.dataframe(pd.DataFrame(status["drift"]))
            st.caption(status["caveat"])
        except requests.RequestException:
            st.warning("Service indisponible.")
