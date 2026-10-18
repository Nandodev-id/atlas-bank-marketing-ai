# Correspondance sujet, canevas et preuves

| Attendu | Section du canevas | Réalisation / preuve |
|---|---|---|
| C1 — besoin et données | 1–2 | Cadrage final, dictionnaire complet, contrôle SHA et source UCI |
| C2 — risques et équité | 1.5, 3.6, 6 | Scénarios S1–S4, tableaux par âge/profession/famille/éducation, limites de proxys |
| C3 — préparation | 3–4 | Pipeline train-only, sentinelle pdays, imputations/encodage, tests de fuite |
| C4 — choix de famille et modèle | 5.0–5.1, 6 | Familles écartées avec motifs ; tableau signature performance/coût/p95/explicabilité |
| C5 — entraînement, CV, évaluation | 5 | 60 fits CV, hyperparamètres, validation et test final distincts, MLflow |
| C6 — service | 8 | FastAPI, entrées strictes, /predict /health, OpenAPI, tests et smoke réel |
| C7 — architecture | 8 | Schéma, hypothèses CPU/RAM, choix hébergement, Docker et CI/CD, rollback |
| C8 — performance et impacts | 6–7, 9 | Scores, calibration, erreurs par groupe, couverture, décision non-promotion, monitoring |
| C9 — évolution continue | 9 | Feedback, déclencheurs, /train candidat séparé, gates, comparaison champion/challenger |
| Communication | 7 | Guide français, plan oral, réponses aux questions, HTML lisible |
| Traçabilité | 0.5 et annexes | Versions, hash, indices figés, journal intégré, inventaire de vérification |

## Distinction réalisé / configuré / non exécuté

**Réalisé et exécuté :** analyse, entraînement, scores, artefact, calibration diagnostique, fairness, OOD, API ASGI, interface AppTest, tests, notebook en IPython séquentiel, figures et HTML.

**Implémenté et vérifié statiquement :** Docker/compose, workflow GitHub, procédure SSH/rollback. Leur exécution réelle demande un Docker accessible et une infrastructure configurée ; ils n'ont pas été lancés ici.

**À ne pas revendiquer :** conformité juridique certifiée, efficacité causale d'une campagne, déploiement externe, CI distante verte, test sous charge réseau, approbation métier/DPO, modèle prêt pour la production.

Les trois gates de production sont négatifs. Le projet démontre une démarche d'ingénierie jusqu'à une décision documentée de non-promotion ; il ne démontre pas un déploiement bancaire réussi.
