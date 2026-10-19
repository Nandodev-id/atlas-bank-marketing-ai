# API Atlas

Point d’entrée : `api/main.py`. Depuis la racine, lancer `python -m uvicorn api.main:app --reload`. Le service réutilise le paquet `bank_marketing.service` ; il ne duplique pas le pipeline de prédiction. Le lancement `python -m bank_marketing.service` reste disponible.

Swagger : http://127.0.0.1:8000/docs. Contrat exporté : `reports/openapi.json`.

Voir `docs/ARCHITECTURE_ET_EXPLOITATION.md` pour l’authentification, l’abstention, l’audit, le feedback et l’entraînement candidat.
