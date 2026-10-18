# Démonstration locale reproductible

Démarrer l'API depuis la racine : `source .venv/bin/activate`, puis `python -m bank_marketing.service`. Swagger : http://127.0.0.1:8000/docs.

Les profils suivants sont choisis **dans le train** uniquement pour montrer les branches du service. Ils ne constituent pas un échantillon d'évaluation ni une preuve de qualité prédictive.

```bash
# Profil historique au score élevé : environ 0,682, prediction=yes, abstain=false.
curl -s http://127.0.0.1:8000/predict -H 'Content-Type: application/json' --data-binary @reports/example_request_high.json

# Profil historique au score faible : environ 0,001, prediction=no, abstain=false.
curl -s http://127.0.0.1:8000/predict -H 'Content-Type: application/json' --data-binary @reports/example_request_low.json

# Valeur Euribor hors domaine : probability=null, abstain=true, human_review.
curl -s http://127.0.0.1:8000/predict -H 'Content-Type: application/json' --data-binary @reports/example_request_ood.json
```

Les réponses réellement obtenues en ASGI sont dans `reports/api_demo_cases.json`. Le request_id change à chaque requête. Si une clé est configurée, ajouter l'en-tête Bearer correspondant ; ne jamais la copier dans le dépôt ou les captures.

Le formulaire Streamlit est lancé par `python -m streamlit run ui/app.py --server.address 127.0.0.1`. Les valeurs médianes par défaut peuvent donner une abstention près du seuil : c'est un comportement prévu. Pour montrer la branche positive, reprendre les huit valeurs de `example_request_high.json`.

Pour le retour observé, utiliser l'UUID renvoyé par votre propre requête, puis POST /feedback avec `request_id` et `outcome` yes/no. Signaler explicitement au jury qu'un retour saisi pendant la démonstration est synthétique. Aucun entraînement automatique n'en découle.

La dernière démonstration est le contrôle de promotion : `python scripts/check_release.py --production` doit terminer en échec et expliquer les trois raisons. Ce refus est le résultat attendu, pas un bug de l'API.
