# Sources et provenance

## Données et sujet

- Sujet Atlas fourni : six pages, dictionnaire des variables et attendus de certification. Le PDF reste local, hors Git.
- CSV `bank-additional-full.csv` : 41 188 observations, 20 prédicteurs et la cible `y`, séparateur `;`.
- SHA-256 : `74adfc578bf77a7ff4bb1ba4a9f8709d9e3c6907342959c2c8416847e0afb4d8`.
- [UCI Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing), Moro, Rita & Cortez (2014), DOI 10.24432/C5K306, licence CC BY 4.0.

## Référentiel

- [Canevas officiel Simplon](https://github.com/Formation-SIMPLON-IA/ia-dev-id-ressources/blob/main/cas_usage_certif/canvas-cas-usage-v2.ipynb), copie non modifiée dans `cas_usage_certif/canvas-cas-usage-v2.ipynb`.
- [Référentiel des compétences](https://github.com/Formation-SIMPLON-IA/ia-dev-id-ressources/blob/main/00_competences_referentiels.md).
- [Aide MLOps et déploiement](https://github.com/Formation-SIMPLON-IA/ia-dev-id-ressources/blob/main/cheatsheet_mlops_deploiement.md).

## Organisation du livrable

Structures consultées le 19 octobre 2026 : [3ti3nne/certif_etienne](https://github.com/3ti3nne/certif_etienne) et [nawellepolin/cas-usage-certif-bank-marketing-nawelle](https://github.com/nawellepolin/cas-usage-certif-bank-marketing-nawelle). Organisation retenue : notebook principal, journal distinct, référence séparée, README technique court et point d’entrée API identifiable. Aucun code ni résultat de ces projets n’a été repris.

## Preuves d’exécution

Le notebook contient les sorties et figures de l’expérience de référence. Ses cellules ont été exécutées séquentiellement dans un namespace IPython neuf via `scripts/execute_notebooks_inprocess.py` ; cette méthode évite les sockets requis par un noyau Jupyter externe. `scripts/execute_notebooks.py` fournit aussi l’exécution avec un noyau externe.

`reports/verification.json` distingue les vérifications exécutées des étapes d’infrastructure non exécutées. Les sources réglementaires figurent dans `ETHIQUE_ET_CONFORMITE.md`.
