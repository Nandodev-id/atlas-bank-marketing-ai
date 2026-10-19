### 5.4 bis — Comparaison stratifiée complémentaire des scénarios

**Analyse exploratoire ajoutée le 19 octobre 2026 après le retour sur la première évaluation.** Elle complète l'étude ; elle ne remplace ni le protocole initial ni le test temporel final. Le candidat servi, ses paramètres et son seuil ne sont pas modifiés.

#### Deux questions distinctes

| Protocole | Population | Question | Limite |
|---|---|---|---|
| CV chronologique initiale | Train initial, premières 60 % des lignes ; trois fenêtres croissantes, gap 100 | Le modèle appris sur une période antérieure généralise-t-il à la suivante ? | Faible diversité de contextes ; scores S2–S4 proches du hasard |
| CV stratifiée complémentaire | Développement : train + calibration + validation, premières 80 % des lignes ; cinq folds mélangés | Les scénarios discriminent-ils lorsque les périodes du développement sont mélangées ? | Ne teste pas le futur ; les mêmes données ont déjà servi à l'étude |
| Test temporel final initial | Dernières 20 % des lignes | Quelle performance hors échantillon après gel du choix ? | Résultat déjà observé ; il ne redevient pas indépendant pour de nouveaux choix |

La CV chronologique permet bien une comparaison **dans une situation de transfert temporel** ; ses scores faibles ne démontrent pas une supériorité fiable d'un scénario. La différence entre CV initiale et complémentaire dépend aussi des **populations et tailles d'entraînement différentes**, pas uniquement du mélange des folds.

#### Protocole complémentaire

32 940 profils après retrait de 10 doublons exacts sur l'ensemble des prédicteurs, sans utiliser la cible pour identifier les doublons. Les 8 238 lignes du test final sont exclues : le script ne lit que le préfixe du CSV antérieur au test, puis sélectionne les indices de développement figés. Aucun identifiant client n'est disponible ; des contacts répétés non identifiables peuvent subsister.

`StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`, mêmes folds pour les huit combinaisons. Deux modèles fixes repris de la grille initiale : LogReg `C=1`, et forêt de 100 arbres, profondeur 8, minimum 10 observations par feuille. Chaque pipeline ajuste imputation, standardisation et encodage uniquement dans le fold d'entraînement. **40 ajustements**, aucun réglage guidé par leurs résultats. Aucune recherche de seuil.

Les colonnes `*_std` sont les écarts-types entre folds, pas des intervalles de confiance. L'AP se compare à la prévalence de 6,38 % sur cette population ; l'AUC à 0,5. S1 conserve `duration` uniquement comme diagnostic de fuite et demeure inutilisable avant appel.

Reproduction indépendante des artefacts de service :

```bash
python -m bank_marketing.modeling.sensitivity --output runtime/sensitivity-reproduction
```

Le script refuse un dossier de sortie non vide. Résultats de référence : `reports/sensitivity/`, avec indices des folds, scores et protocole daté.

#### Lecture des résultats

| Scénario | AUC LogReg | AUC forêt | AP LogReg | AP forêt |
|---|---:|---:|---:|---:|
| S1 — avec duration | 0,946 | 0,940 | 0,505 | 0,515 |
| S2 — sans duration | 0,670 | 0,685 | 0,205 | 0,218 |
| S3 — retrait démographique | 0,672 | 0,687 | 0,204 | 0,217 |
| S4 — huit variables | 0,641 | 0,676 | 0,154 | 0,201 |

Le tableau exécuté ci-dessous donne aussi la dispersion. Sur ce périmètre, les scores ne sont pas proches de 0,80 : la comparaison porte sur le développement, pas sur le fichier complet. Il existe un signal lorsque les périodes sont mélangées, mais la robustesse temporelle reste insuffisante. S2 et S3 sont descriptivement proches ; aucune supériorité statistique n'est établie. S4 sacrifie une partie de l'AP pour réduire les entrées. Ces observations ne servent pas à remplacer le candidat ni à annoncer un nouveau score sur le test.

#### Interprétation du contexte, de S4 et du seuil

Le train initial a un Euribor compris entre **4,191 et 5,045**, contre **1,299 à 1,410** sur la validation initiale. Cela établit un changement de contexte macroéconomique ; ce fichier ne contient pas de dates complètes permettant de qualifier précisément chaque bloc « avant/après la crise de 2008 ». Les plages du développement sont archivées dans `development_macro_ranges.csv`.

**S4 est le candidat minimisé retenu par la règle préétablie, pas un gagnant prédictif démontré.** La tolérance de 0,02 AP et la priorité au nombre de variables l'ont retenu parmi des modèles faibles en CV temporelle. Une future sélection doit exiger un gain stable par rapport à la baseline avant de départager les candidats par minimisation.

Les cinq importances par permutation macro sont nulles **sur la validation initiale, pour ce modèle et le score AP**. Deux variables y sont constantes et d'autres prennent des valeurs éloignées du train. Une importance nulle sur ce bloc ne prouve ni que la forêt n'utilise jamais la variable, ni son inutilité dans une population plus diverse. Les variables corrélées compliquent aussi cette interprétation.

Le seuil **0,05 est la borne basse de la grille** choisie pour maximiser le F1 de validation. Il s'agit d'un signal de fragilité, pas d'un optimum métier universel. Le seuil reste gelé ; une future recherche utilisera un nouveau protocole, des coûts ou une capacité d'appels explicites et des données indépendantes. Le budget top 20 % et ce seuil sont deux règles différentes.

Enfin, **100 % du test est rejeté par le filtre OOD**. C'est un échec de couverture opérationnelle. Nous ne supprimons pas ce filtre pour rendre artificiellement le service utilisable : toute nouvelle politique doit être évaluée avec des données représentatives avant promotion.
