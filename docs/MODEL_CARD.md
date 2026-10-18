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
