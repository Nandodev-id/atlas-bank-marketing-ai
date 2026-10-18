> Historique de la première étape, conservé pour traçabilité. Pour l’état final, lire le README, le notebook de certification et `COUVERTURE_EXAMEN.md`.

# Audit et progression vers l'oral — 18 octobre 2026

## Sources réellement consultées

- Sujet fourni : `Sujet_Examen_Atlas_IA_Marketing_Bancaire.pdf`, six pages lues.
- CSV fourni à la racine et copie dans `data/raw/` : contenus identiques, SHA-256 conforme au manifeste existant.
- [Canevas officiel](https://github.com/Formation-SIMPLON-IA/ia-dev-id-ressources/blob/main/cas_usage_certif/canvas-cas-usage-v2.ipynb), récupéré via le connecteur GitHub le 18 octobre 2026. Copie locale : `notebooks/simplon_reference_canvas.ipynb` (50 cellules). Le téléchargement direct par le script a échoué à cause du réseau de cet environnement ; le connecteur a permis la récupération.

## Situation vérifiée

| Élément | État au début de cette session |
|---|---|
| Git local | Commit `73d1ac2`, arbre de travail propre |
| Remote configuré | `https://github.com/Nandodev-id/atlas-bank-marketing-ai.git` ; synchronisation, visibilité et CI distante non vérifiées |
| Données | 41 188 lignes, 20 variables explicatives et cible `y` |
| Cible | 36 548 non, 4 640 oui (11,27 %) |
| Qualité | 12 lignes dupliquées exactes ; 39 673 occurrences de `pdays=999` |
| Valeurs `unknown` | default : 8 597 ; education : 1 731 ; housing et loan : 990 chacun ; job : 330 ; marital : 80 |
| Code existant | Contrat de colonnes, inspection CSV et tests associés |
| Notebook initial | Squelette de 12 cellules, sans analyse exécutée |
| Modèles / API / monitoring | Non implémentés ; dossiers API et monitoring contiennent des notes |
| Environnement | Python 3.11 disponible ; pandas et pytest absents de l'interpréteur inspecté |

Ne pas supprimer automatiquement les doublons : sans identifiant client, deux lignes identiques ne prouvent pas une erreur de saisie. `unknown` et `pdays=999` demandent une interprétation métier avant transformation.

## Travail réalisé pendant cette session

- Contrôle du CSV exécuté avec succès, y compris son empreinte.
- Canevas complet enregistré comme référence ; copie de travail dans `notebooks/certification.ipynb`.
- Ancien notebook conservé dans `notebooks/certification_foundation_backup.ipynb`.
- Section 1 rédigée en français et fiche d'explication dans `docs/ETAPE_01_CADRAGE.md`.
- JSON des notebooks et syntaxe Python vérifiés. Exécution complète et pytest non réalisés : dépendances manquantes et sections futures encore à compléter.

## Ordre de travail, avec explication à chaque étape

| Étape | Sections du canevas | Preuve attendue / question d'oral |
|---|---|---|
| 1. Cadrage — rédigé | 1 | Qui utilise la solution, quand et pour quelle décision ? |
| 2. Environnement, provenance, EDA | 0, 0.5, 2, 3 | Notebook exécuté, dictionnaire complet, qualité, déséquilibre et biais observés |
| 3. Préparation et protocole | 4 | Découpage justifié, test réservé, transformations ajustées sur entraînement uniquement |
| 4. Modèles et scénarios | 5, 6 | Dummy, régression logistique, forêt aléatoire ; CV comparable ; S1 toutes variables, S2 sans duration, S3 sans duration et variables discutables ; S4 optionnel |
| 5. Interprétation et équité | 6, 7 | Comparaison des erreurs, sous-groupes, coût, latence, explicabilité, choix final et recours humain |
| 6. Service et architecture | 8 | API /predict et /health, validation, erreurs, journaux maîtrisés, tests, schéma CPU/RAM et hébergement |
| 7. Suivi et évolution | 9 | Indicateurs, tableau de bord, feedback, déclencheurs de réentraînement, CI/CD et champion/challenger |
| 8. Répétition orale | 7 + annexes | Exécution propre, journal intégré au notebook final, démonstration et questions du jury |

Le sujet d'examen impose S1–S3 ; S4 est optionnel. Docker, MLflow et interface de saisie sont des bonus dans le PDF, mais le canevas les inclut dans ses attentes d'industrialisation : nous les gardons dans le plan pour suivre les deux sources. La route /train est mentionnée dans le canevas ; le minimum explicite du PDF est /predict et /health. Les numéros de scénarios du PDF priment sur les exemples génériques du canevas.

Pour un oral mardi 20 octobre, priorité dimanche au cadrage, aux données et au protocole ; lundi aux comparaisons, au service et aux preuves de suivi ; mardi à la répétition. Ce calendrier est une proposition, pas une promesse que les étapes manquantes sont déjà réalisées.

## Points à résoudre lors des prochaines étapes

- Installer l'environnement du projet ; inclure matplotlib et seaborn utilisés par le canevas, actuellement absents du manifeste.
- Vérifier la provenance et l'ordre temporel avant de figer le split. Une absence de date complète limite les conclusions temporelles.
- Réserver les données de test avant l'exploration détaillée et le choix des modèles. Les statistiques globales ci-dessus ont déjà été examinées et doivent être déclarées.
- Vérifier les sources juridiques officielles pour l'analyse RGPD ; ne pas confondre variables discutables et catégories particulières au sens légal.
- Définir les objectifs et seuils avant l'ouverture du test final ; aucun score de modèle à annoncer pour le moment.
