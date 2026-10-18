# Comprendre et présenter le code

## 1. Architecture : pourquoi cette structure ?

Les anciens exercices ne prescrivent pas tous la même architecture : M1-B2 utilise `app/` pour son API ; M0-B2 sépare API et Streamlit dans `services/` ; le brief M5-B1 demande explicitement model/backend/frontend. Cette dernière organisation répond à ce brief particulier.

Le canevas officiel `cas_usage_certif/canvas-cas-usage-v2.ipynb`, section 8, demande une API, une interface, des tests, Docker, CI/CD et une justification d'architecture. Il n'impose pas de recopier les trois services de M5. Dans Atlas, FastAPI assure déjà le rôle de backend. Ajouter un backend qui transmet seulement les requêtes augmenterait la complexité.

```text
Navigateur → Streamlit (ui/app.py, port 8501)
                     → HTTP → FastAPI (service/app.py, port 8000)
                                      → pipeline sklearn chargé en mémoire
                                      → SQLite : audit et feedback
CSV → modeling/train.py → artefact joblib + rapports + MLflow
```

`src/bank_marketing` est un paquet Python installé avec `pip install -e .`. `data`, `modeling`, `service` et `monitoring` séparent les responsabilités. Les dossiers de code ne sont pas obligatoirement des conteneurs. Docker Compose définit deux services, `api` et `ui`. L'entraînement reste un travail hors ligne ; il ne se répète pas à chaque prédiction.

## 2. Commencer par la question métier

On estime la probabilité de souscription à un dépôt à terme. La cible du CSV est `y` : yes = souscription, no = absence de souscription. Une probabilité n'est ni une certitude ni une autorisation de contacter une personne.

## 3. Lire les données

Ouvrir `src/bank_marketing/data/schema.py`, puis `inspection.py`. Le premier décrit les colonnes attendues ; le second contrôle le CSV, les types, les catégories et la cible. Le fichier contient 41 188 lignes. Le hash identifie précisément le fichier utilisé.

`default` signifie **crédit en défaut de paiement**. Ce n'est pas une valeur par défaut du logiciel. Ses valeurs réelles sont : no = 32 588, unknown = 8 597, yes = 3. Unknown signifie information inconnue, et ne doit pas être remplacé par no. Avec seulement trois yes, on ne peut pas conclure à une performance fiable pour cette catégorie. Dans l'interface, les libellés français correspondent aux codes originaux envoyés à l'API.

## 4. Comprendre le protocole avant le modèle

Lire `config/protocol.json`, puis `src/bank_marketing/modeling/train.py`. On sépare les données dans leur ordre temporel : 60 % entraînement, 10 % calibration, 10 % validation, 20 % test final. Le test final sert à évaluer le choix fixé, pas à chercher les meilleurs paramètres.

La validation croisée utilise trois fenêtres croissantes et un écart de 100 lignes. Quatre scénarios comparent différentes informations disponibles. `duration` est exclue du scénario exploitable avant appel : la durée n'est connue qu'après l'appel. Son utilisation donnerait une évaluation trop optimiste pour cet usage.

## 5. Lire le pipeline

Ouvrir `src/bank_marketing/modeling/core.py`. Les transformations des variables et le classifieur sont réunis dans un pipeline sklearn. Elles sont apprises sur l'entraînement et réutilisées à l'identique sur les autres blocs et en service.

Le scénario retenu, S4, utilise huit variables : default, housing, loan, emp.var.rate, cons.price.idx, cons.conf.idx, euribor3m, nr.employed. La forêt possède 100 arbres, une profondeur maximale de 8 et au moins 10 observations par feuille. Le seuil de décision de 0,05 provient de la validation. Le seuil n'est pas la probabilité calculée : il sert à convertir un score en classe.

## 6. Expliquer les résultats avec leurs limites

Lire `reports/final_test.json` et `docs/MODEL_CARD.md`. Sur le test final, avant abstention, AP ≈ 0,443, ROC-AUC ≈ 0,694, précision ≈ 40 %, rappel ≈ 89 %. Le rappel élevé s'accompagne de nombreux faux positifs. La prévalence varie fortement selon les blocs : la qualité future n'est pas garantie par un score global.

Le contrôle hors distribution rejette tous les profils du test final. La couverture opérationnelle vaut donc 0 %. Les métriques précédentes décrivent le modèle sans ce filtre, pas des décisions réellement servies. La conclusion honnête est : prototype logiciel fonctionnel, candidat non validé pour la production. La calibration testée a été rejetée ; ne pas présenter les probabilités comme parfaitement calibrées.

## 7. Suivre une requête API

Lire `src/bank_marketing/service/__main__.py`, puis `app.py`.

1. Le lancement démarre Uvicorn et crée l'application FastAPI.
2. Au démarrage, l'application vérifie l'artefact et charge le pipeline une seule fois.
3. `GET /health` permet de vérifier le chargement du service.
4. `POST /predict` reçoit un JSON. Pydantic et `validate_features` contrôlent sa structure, les types et les huit variables.
5. `ood_reasons` vérifie les plages et catégories apprises. Un profil hors distribution déclenche une abstention.
6. Pour un profil accepté, le pipeline calcule une probabilité. Une règle de proximité du seuil peut aussi demander une revue humaine.
7. La réponse contient le résultat et un identifiant de requête ; `store.py` enregistre l'audit. Le service ne déclenche aucun appel commercial.

Une erreur de contrat donne 422. Une abstention métier donne 200 avec `abstain=true` et `probability=null` : la requête a été traitée, mais aucune estimation exploitable n'est émise.

## 8. Suivre l'interface

Lire `ui/app.py`. Les champs collectent les huit variables, construisent le JSON puis appellent l'API par HTTP. Streamlit affiche la réponse ; il n'entraîne pas le modèle. Les autres onglets montrent les rapports et le suivi. Dans Compose, `http://api:8000` utilise le nom du service sur le réseau interne ; en lancement local, on utilise localhost.

## 9. Expliquer feedback et suivi

Lire `service/store.py` et `monitoring/checks.py`. Le feedback rattache un résultat observé à une requête. Les indicateurs suivent les entrées, les erreurs et, lorsque les labels arrivent, la qualité prédictive. Une dérive déclenche une investigation ; elle ne prouve pas automatiquement qu'il faut remplacer le modèle. `/train` prépare un candidat séparé sur un snapshot approuvé, sans écraser le modèle servi.

## 10. Expliquer les preuves logicielles

Lire `tests/`, `.github/workflows/ci.yml`, puis `candidate.yml`. Les tests contrôlent notamment les contrats HTTP, les erreurs, l'abstention et les contrôles de promotion. La CI relance les tests sur GitHub. Le pipeline candidat distingue qualité logicielle et validation du modèle. Des tests verts ne suffisent pas à autoriser la production.

Les vérifications locales utilisent FastAPI TestClient et Streamlit AppTest. Elles ne constituent pas un test Docker ni un test de charge réseau. Le déploiement réel reste conditionné à un candidat validé et à une infrastructure configurée.

## Démonstration de cinq minutes

Ouvrir Swagger et `/health`, puis l'interface. Tester un exemple accepté, un exemple hors distribution, et une entrée invalide dans Swagger. Montrer ensuite la model card et expliquer pourquoi la production est bloquée. Terminer par les prochaines étapes : données récentes représentatives, protocole figé à l'avance, nouvelle évaluation temporelle, revue métier et conformité.

Phrase pour le jury : « J'ai séparé l'entraînement, le service de prédiction et l'interface. Les contrôles montrent que le logiciel fonctionne, mais aussi que ce candidat ne couvre pas la population du test final. Je recommande donc de ne pas le promouvoir en production. »
