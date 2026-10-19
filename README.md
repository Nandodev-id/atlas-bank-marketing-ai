# Atlas — marketing bancaire responsable

Cas d’usage de certification Dev-id / Simplon, à partir du jeu public **UCI Bank Marketing**. Objectif : estimer la souscription à un dépôt à terme avec les informations disponibles avant l’appel, comparer les scénarios de variables et exposer le pipeline retenu via une API.

Le livrable principal est [notebooks/certification.ipynb](notebooks/certification.ipynb), également disponible en [HTML](reports/certification.html). Les étapes et décisions sont consignées dans le [journal de bord](notebooks/journal-de-bord.ipynb).

## Structure

```text
notebooks/          certification, exploration et journal de bord
cas_usage_certif/   canevas officiel Simplon, non modifié
src/bank_marketing/
  data/             schéma et contrôles du CSV
  modeling/         préparation, entraînement et évaluation
  service/          validation HTTP, prédiction, audit et feedback
  monitoring/       dérive et indicateurs de réentraînement
api/main.py         point d’entrée FastAPI
ui/                 interface Streamlit et image Docker dédiée
config/             protocole expérimental
reports/            métriques, figures, OpenAPI et preuves d’exécution
artifacts/          pipeline et références locales, hors Git
data/raw/           CSV local, hors Git
scripts/            reproduction, vérification et déploiement
tests/             tests automatisés
docs/              cadrage, données, architecture et model card
.github/workflows/  CI et évaluation des candidats
```

## Installation

Python 3.12, depuis la racine du projet :

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-tested.txt
python -m pip install --no-deps -e .
```

## Données et modèle

Le CSV et le modèle sont exclus de Git. Sur une copie qui possède déjà `artifacts/model.joblib`, passer directement au lancement de l’API.

Depuis un clone neuf :

```bash
python scripts/fetch_dataset.py
python -m bank_marketing.data.inspection
python -m bank_marketing.modeling.train --output runtime/reproduction/reports --artifacts artifacts
```

Le téléchargement vérifie le SHA-256 attendu. L’entraînement conserve les rapports versionnés et écrit les nouveaux résultats dans `runtime/reproduction/reports`. Une reproduction sur le même jeu de test ne constitue pas une nouvelle validation indépendante. Les versions testées figurent dans `requirements-tested.txt`.

## API et interface

Premier terminal, environnement activé :

```bash
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger : http://127.0.0.1:8000/docs — santé : http://127.0.0.1:8000/health.
Le lancement `python -m bank_marketing.service` reste disponible.

Second terminal :

```bash
source .venv/bin/activate
python -m streamlit run ui/app.py --server.address 127.0.0.1
```

Interface : http://127.0.0.1:8501. Pour authentifier les requêtes, définir la même variable `ATLAS_API_KEY` dans les deux terminaux.

```bash
curl -s http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  --data-binary @reports/example_request.json
```

Avec une clé configurée, ajouter un en-tête `Authorization: Bearer ...`.

## Docker

Le modèle et ses fichiers de référence doivent être présents dans `artifacts/` avant la construction.

```bash
export ATLAS_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up --build
```

Compose définit deux services : API sur 8000 et Streamlit sur 8501. La configuration a été validée ; la construction et l’exécution des images restent à vérifier.

## Vérification

```bash
python -m pytest -q
python scripts/smoke_api.py
python scripts/smoke_ui.py
python scripts/check_release.py
# Échec attendu pour le candidat actuel :
python scripts/check_release.py --production
```

Les tests HTTP utilisent FastAPI TestClient ; ceux de l’interface utilisent Streamlit AppTest. Ils ne remplacent pas un test réseau sous charge. La CI exécute les tests et compile le code. Le workflow candidat applique les contrôles avant une éventuelle promotion.

## Résultats et limites

Le candidat S4 utilise huit variables et une forêt de 100 arbres, profondeur 8, avec un seuil de 0,05. Sur le test temporel final, **avant abstention** : ROC-AUC 0,694 ; AP 0,443 ; précision 40,31 % ; rappel 88,98 %.

**Le candidat n’est pas validé pour la production.** La validation temporelle est faible, des écarts entre groupes persistent et le filtre hors distribution s’abstient sur tout le bloc final : couverture opérationnelle de 0 %. Le service ne fournit aucune autorisation de contact commercial.

- [Model card](docs/MODEL_CARD.md)
- [Architecture et exploitation](docs/ARCHITECTURE_ET_EXPLOITATION.md)
- [Dictionnaire des données](docs/DICTIONNAIRE_DONNEES.md)
- [Éthique et conformité](docs/ETHIQUE_ET_CONFORMITE.md)
- [Correspondance avec le canevas](docs/COUVERTURE_EXAMEN.md)
- [Sources](docs/SOURCES.md)

Source des données : Moro, Rita & Cortez (2014), UCI Bank Marketing, DOI 10.24432/C5K306, licence CC BY 4.0.
