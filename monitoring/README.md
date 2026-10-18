# Monitoring Atlas

Implémentation : `src/bank_marketing/monitoring/checks.py`. Routes `/monitoring` et `/metrics`, affichage dans l'onglet Streamlit « Suivi du service ». PSI sur les entrées après 100 requêtes ; AP/Brier avec labels retardés ; demande de réentraînement après 200 labels et deux classes si AP se dégrade. Aucune promotion automatique.

Les seuils, leur caractère pédagogique, les biais de collecte et le plan de reprise figurent dans `docs/ARCHITECTURE_ET_EXPLOITATION.md`. Les preuves historiques sont distinctes des retours synthétiques de smoke test et d'un futur suivi réel.
