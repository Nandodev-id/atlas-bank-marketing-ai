# Model card — candidat Atlas

- Usage : démonstration de classement de propension à souscrire un dépôt à terme avant contact.
- Non-usages : crédit, éligibilité à un produit, décision autonome, preuve de consentement, campagne réelle avec ce candidat.
- Source : UCI Bank Marketing, variante additionnelle complète, banque portugaise 2008–2010 ; SHA dans metadata.
- Modèle : RandomForestClassifier, 100 arbres, profondeur 8, minimum 10 observations par feuille, seed 42 ; scénario S4 à huit entrées.
- Prétraitement : imputation, standardisation des nombres et one-hot des catégories, ajustés dans les folds ; pipeline sérialisé.
- Entraînement : premières 24 712 lignes ; calibration 4 119 ; validation 4 119 ; test 8 238. Aucun réajustement sur test.
- Seuil : 0,05, choisi par F1 de validation ; calibration sigmoid rejetée pour pente négative.
- Test hors filtre : AP 0,443, ROC-AUC 0,694, F1 0,555, precision@20 0,441, lift@20 1,43.
- Validation : AP 0,108 sous prévalence 0,120 ; instabilité non résolue.
- Couverture du service sur test : 0 %. Toutes les lignes présentent une valeur hors plage d'entraînement.
- Équité : différences importantes de FPR/FNR et sélection malgré retrait des attributs de groupe. Petits groupes signalés.
- Limites : ancienneté, sélection des clients déjà contactés, labels non causaux, dates et identifiants incomplets, contexte macro changeant, seuil non optimisé pour un coût métier inconnu.
- Décision : **ne pas promouvoir**. Recueillir données récentes, revoir le protocole en backtests et évaluer sur un nouveau test.
- Propriétaire opérationnel à désigner : responsable campagne ; partenaires SI/DPO avant usage.

## Analyse complémentaire du 19 octobre 2026

CV stratifiée à cinq folds sur train + calibration + validation, après retrait de 10 profils dupliqués : 32 940 lignes ; test final exclu. Deux modèles fixes par scénario, 40 fits. AUC des forêts S2/S3/S4 : 0,685 / 0,687 / 0,676. Cette analyse exploratoire ne remplace pas le test temporel initial et ne démontre pas une généralisation future. Les populations et tailles de folds diffèrent de la CV chronologique initiale.

S4 a été retenu par minimisation parmi des candidats faibles en CV temporelle ; il n'est pas un gagnant prédictif établi. Le seuil 0,05 est la borne basse de la grille et reste inchangé. Les importances macro nulles par permutation sur validation ne prouvent pas une inutilité générale.

Chez les plus de 60 ans, 755/767 profils sont sélectionnés avant abstention et le FPR vaut 399/411 (97,08 %). **Aucune campagne sur ce score** ; nouvelle évaluation temporelle et par groupe, avec incertitudes et critères définis avant expérience, puis revue métier/SI/DPO sur un nouveau test indépendant. Voir `DECISION_EQUITE.md`, `ANALYSE_COMPLEMENTAIRE.md` et les sections 5.4 bis, 6.4–6.5 du notebook.
