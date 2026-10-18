# Atlas — marketing bancaire responsable

Projet de certification Simplon / OPCO Atlas, compétences C1–C9. **Le projet local est implémenté et évalué ; le candidat ne doit pas être promu en production.** Les résultats, leur interprétation et les limites sont documentés, sans score inventé.

## Commencer par ces fichiers

- [Notebook de certification complet](notebooks/certification.ipynb) — toutes les sections du canevas, sorties et figures incorporées.
- [Version HTML à ouvrir dans un navigateur](reports/certification.html) — lecture sans Jupyter.
- [Guide oral pas à pas en français](docs/GUIDE_ORAL_PAS_A_PAS.md) — explications, démonstration et questions du jury.
- [Model card](docs/MODEL_CARD.md), [architecture et exploitation](docs/ARCHITECTURE_ET_EXPLOITATION.md), [éthique et conformité](docs/ETHIQUE_ET_CONFORMITE.md).
- [Canevas officiel original](notebooks/simplon_reference_canvas.ipynb), issu de [cas_usage_certif/canvas-cas-usage-v2.ipynb](https://github.com/Formation-SIMPLON-IA/ia-dev-id-ressources/blob/main/cas_usage_certif/canvas-cas-usage-v2.ipynb).

- [Lecture du code et comparaison des architectures](docs/LECTURE_CODE_PAS_A_PAS.md) — parcours de préparation à l’oral.

## Résultat principal

60 ajustements de validation croisée : quatre scénarios × cinq configurations × trois folds temporels. Le candidat minimisé S4 est une forêt de 100 arbres, profondeur 8, huit variables, seuil 0,05.

| Test final, sans filtre d'abstention | Valeur |
|---|---:|
| ROC-AUC | 0,694 |
| Average precision | 0,443 |
| Prévalence / référence AP | 0,308 |
| Précision / rappel | 40,31 % / 88,98 % |
| F1 | 55,49 % |
| Lift parmi les 20 % prioritaires | 1,43× |

**Pourquoi ne pas déployer ?** La validation est sous sa référence AP, les erreurs varient fortement entre groupes et la politique OOD s'abstient sur 100 % du bloc final. La couverture opérationnelle est donc nulle. Les scores ci-dessus ne sont pas ceux de décisions émises par le service. Ne pas confondre une API fonctionnelle et un modèle validé pour une campagne réelle.

## Environnement

Sur ce Mac, `.venv` existe déjà, adossé en lecture aux paquets Anaconda installés :

```bash
cd /Users/fernando/Documents/devid/formation-ai/atlas-bank-marketing-ai
source .venv/bin/activate
python -m pytest -q
```

Sur une autre machine, Python **3.12** conseillé pour les versions testées :

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-tested.txt
python -m pip install --no-deps -e .
python -m ipykernel install --prefix .venv --name atlas --display-name 'Atlas Python'
```

Les dépendances directes sont figées dans `requirements-tested.txt`. L'inventaire complet de l'environnement observé est dans `reports/environment_all_packages.json` ; ce n'est pas un lock transplateforme des dépendances transitives.

## Démonstration locale

Terminal 1 :

```bash
source .venv/bin/activate
python -m bank_marketing.service
```

Ouvrir `http://127.0.0.1:8000/docs` pour Swagger. Terminal 2 :

```bash
source .venv/bin/activate
python -m streamlit run ui/app.py --server.address 127.0.0.1
```

Ouvrir `http://127.0.0.1:8501`. Le mode local fonctionne sans clé, uniquement sur localhost. Pour activer l'authentification, définir `ATLAS_API_KEY` dans les deux terminaux. Le mode `ATLAS_ENV=production` impose une clé et ne signifie pas que le modèle est approuvé.

Exemple d'appel :

```bash
curl -s http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  --data-binary @reports/example_request.json
```

Si une clé est configurée, ajouter un en-tête Bearer. Ne pas envoyer de données réelles pour la démonstration. Le système n'autorise jamais automatiquement le démarchage.

Pour lancer les deux services avec Docker sur ce Mac (artefacts déjà présents) :

```bash
export ATLAS_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up --build
```

L'interface reste sur le port 8501 et l'API sur 8000. Sur un clone neuf, produire ou récupérer les artefacts approuvés avant de construire l'image API. La configuration Compose a été validée ; la construction et l'exécution Docker restent à tester sur votre machine.

## Données et reproduction

Le CSV original est dans `data/raw/` sur ce Mac et dans le ZIP de rendu. Il est exclu de Git. Pour un clone neuf :

```bash
python scripts/fetch_dataset.py
python -m bank_marketing.data.inspection
```

Le téléchargement contrôle le SHA-256 attendu. Citation : Moro, S., Rita, P., & Cortez, P. (2014), Bank Marketing, UCI, DOI 10.24432/C5K306 ; licence CC BY 4.0.

L'expérience est déjà exécutée. Pour la reproduire depuis un clone sans résultats runtime, **archiver les rapports fournis** puis :

```bash
# Le script refuse volontairement d'écraser reports/final_test.json.
python -m bank_marketing.modeling.train
python scripts/build_reports.py
python scripts/benchmark_operations.py
python scripts/freeze_environment.py
python scripts/evaluate_candidate.py
python scripts/smoke_api.py
python scripts/smoke_ui.py
python scripts/build_notebook.py
python scripts/execute_notebooks.py
```

Pour une nouvelle expérimentation, utiliser `--output runtime/experience-02/reports --artifacts runtime/experience-02/artifacts` et documenter la passe ; ne pas remplacer les preuves de la première évaluation. `build_reports.py` et le notebook principal lisent les résultats de référence à la racine. Les scripts de candidate evaluation acceptent un autre dossier. Une répétition de reproduction sur le même test n'est pas une nouvelle validation indépendante.

La session Codex interdit les sockets Jupyter : les 21 cellules de code de certification et les 9 cellules d'exploration ont été exécutées séquentiellement avec `scripts/execute_notebooks_inprocess.py`, en namespace IPython neuf. Les figures et sorties sont réelles. `execute_notebooks.py` fournit la vérification avec noyau externe sur une machine qui l'autorise.

## Vérification et preuves

```bash
python -m pytest -q
python scripts/smoke_api.py
python scripts/smoke_ui.py
python scripts/check_release.py
# Échec attendu pour ce candidat :
python scripts/check_release.py --production
```

Les tests API utilisent ASGI TestClient ; l'interface utilise Streamlit AppTest relié à l'API réelle en mémoire. Les latences sont séquentielles et locales, sans réseau ni charge concurrente. `reports/verification.json` précise ce qui a été exécuté. Aucun Docker, run GitHub Actions distant ou hébergement réel n'est revendiqué.

## Industrialisation

- `/predict`, `/health`, `/model`, `/feedback`, `/monitoring`, `/metrics`, `/train`, `/jobs/{id}`.
- Modèle complet + hash ; validation stricte ; logs structurés ; audit SQLite restreint et durée limitée.
- MLflow local : `python -m mlflow ui --backend-store-uri ./mlruns --host 127.0.0.1`.
- `docker-compose.yml` : deux services API + Streamlit, clé requise, non-root, stockage audit séparé, CPU/RAM limités.
- CI : tests et compilation. Pipeline candidat : snapshot approuvé, entraînement, évaluation, comparaison champion/challenger si configurée, gate de promotion, environnement GitHub production.
- Déploiement activé seulement si hôte, champion et fenêtre commune approuvée sont configurés. Le script serveur teste la santé puis restaure l'image précédente en cas d'échec.

Dépôt distant configuré : https://github.com/Nandodev-id/atlas-bank-marketing-ai. La publication depuis cette session est bloquée : DNS indisponible dans le terminal et permission d’écriture refusée (403) par l’intégration GitHub. Les modifications sont préparées pour un `git push origin main` depuis le terminal VS Code. Aucun déploiement réel n’est revendiqué. Pour la production, configurer l'approbation de l'environnement GitHub, les secrets SSH et le contrôle des droits de contact ; surtout, fournir un **nouveau candidat qui passe les contrôles**.

## Structure

```text
config/                 protocole initial
src/bank_marketing/      inspection, modèle, monitoring, API
notebooks/              rendu complet, exploration et référence
reports/                scores, figures, OpenAPI, HTML, preuves
artifacts/              modèle et données de référence locales (hors Git)
ui/                     interface Streamlit
scripts/                reproduction, contrôles, déploiement
 tests/                 tests automatisés
.github/workflows/      CI et cycle candidat
 docs/                  guide oral, décisions et conformité
```

`docs/AUDIT_ET_PLAN_ORAL.md`, `SESSION_01.md` et `ETAPE_01_CADRAGE.md` conservent l'historique initial ; ce README, le notebook final et la model card décrivent l'état actuel.
