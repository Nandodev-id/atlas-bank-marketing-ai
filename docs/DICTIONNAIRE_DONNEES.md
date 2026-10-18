# Dictionnaire du sujet

| Variable | Signification et valeurs | Type | Disponibilité / vigilance |
|---|---|---|---|
| age | Âge en années | numérique | Personnel, risque de ciblage par âge ; exclu S3/S4 |
| job | Profession : admin., blue-collar, etc., unknown | catégorie | Proxy social ; exclu S3/S4 |
| marital | married, single, divorced (inclut veuf), unknown | catégorie | Situation familiale ; exclu S3/S4 |
| education | basic.4y/6y/9y, high.school, illiterate, professional.course, university.degree, unknown | catégorie | Proxy social ; exclu S3/S4 |
| default | Crédit en défaut : yes/no/unknown | catégorie | Situation bancaire, sensible au sens courant |
| housing | Prêt immobilier : yes/no/unknown | catégorie | Information bancaire |
| loan | Prêt personnel : yes/no/unknown | catégorie | Information bancaire |
| contact | cellular/telephone | catégorie | Doit correspondre au canal prévu avant appel |
| month | Mois du contact | catégorie | Utiliser le mois planifié ; ne pas trier par nom de mois |
| day_of_week | mon/tue/wed/thu/fri | catégorie | Jour prévu avant appel |
| duration | Durée du dernier appel en secondes | numérique | Inconnue avant appel : fuite pour notre usage |
| campaign | Nombre de contacts, appel courant inclus | entier | À reconstruire comme rang de l'appel prévu |
| pdays | Jours depuis contact de campagne antérieure, 999 = absence | entier codé | 999 n'est pas une durée réelle |
| previous | Nombre de contacts avant campagne actuelle | entier | Historique connu |
| poutcome | failure/nonexistent/success | catégorie | Résultat de campagne précédente |
| emp.var.rate | Variation de l'emploi, trimestrielle | numérique | Date de publication à vérifier |
| cons.price.idx | Indice prix consommation, mensuel | numérique | Valeur disponible à la date de décision |
| cons.conf.idx | Confiance consommateurs, mensuelle | numérique | Idem ; valeurs négatives légitimes |
| euribor3m | Euribor trois mois, quotidien | numérique | Contexte macroéconomique historique |
| nr.employed | Nombre de salariés, trimestriel | numérique | Indicateur macro, pas taille de notre échantillon |
| y | Dépôt souscrit : yes/no | cible binaire | Résultat futur, jamais une entrée du modèle |
