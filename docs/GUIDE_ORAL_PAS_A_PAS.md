# Comprendre et présenter Atlas — guide pas à pas

Ce guide explique le travail réalisé, les fichiers à ouvrir et les limites à assumer. Il est conçu pour être reformulé à l'oral, pas récité sans compréhension. Les chiffres proviennent de `reports/` et du notebook exécuté.

## 1. Partir du problème métier

Une banque propose un dépôt à terme par téléphone. Chaque appel coûte du temps et peut gêner un client peu intéressé. Le besoin consiste à prioriser les contacts, pas à remplacer toute décision commerciale.

**Notre question IA :** « À partir d'informations connues avant l'appel, quelle est la probabilité de souscription ? » La cible est `y`, avec deux réponses : `yes` et `no`. C'est une **classification binaire supervisée** : binaire car il existe deux classes ; supervisée car les exemples historiques possèdent déjà leur résultat.

Un score ne dit pas que l'appel **cause** une souscription. Une personne pourrait souscrire sans cet appel. Pour mesurer l'effet causal ou le gain réel, il faudrait une campagne contrôlée avec un groupe comparable et les validations nécessaires.

À dire : « Je construis une aide à la priorisation des contacts, pas un système d'attribution de crédit ni une autorisation de démarcher. »

## 2. Comprendre les données avant de coder un modèle

Le fichier fourni contient **41 188 observations**, **20 variables explicatives** et **une cible**. Les lignes correspondent aux observations de contacts du dataset ; sans identifiant client, on ne peut pas affirmer qu'il s'agit de 41 188 personnes distinctes.

Les variables se répartissent en quatre groupes :

1. Profil : âge, profession, situation familiale, éducation.
2. Situation bancaire : défaut de paiement, prêt immobilier, prêt personnel.
3. Contacts et campagnes : canal, date partielle, durée, nombre de contacts, historique.
4. Contexte économique : variation de l'emploi, prix, confiance, Euribor, nombre de salariés.

Le séparateur CSV est `;`. Une lecture sans ce paramètre pourrait charger une seule grande colonne. L'empreinte SHA-256 permet de vérifier que nous travaillons toujours sur les mêmes octets. Ce hash n'anonymise rien : il contrôle l'intégrité du fichier.

UCI confirme que cette variante est ordonnée par date, de mai 2008 à novembre 2010. C'est une source ancienne, portugaise, dont la représentativité pour une banque actuelle n'est pas démontrée. Le dictionnaire du PDF est utilisé pour cette variante ; ne pas mélanger avec les autres variantes UCI.

À ouvrir : `docs/DICTIONNAIRE_DONNEES.md` et §2 du notebook.

## 3. Pourquoi une accuracy élevée peut être trompeuse

Dans l'ensemble du fichier, **4 640 observations positives**, soit **11,27 %**. Un modèle qui répond toujours « non » atteint **88,73 % d'accuracy**, mais ne repère aucun souscripteur.

Imagine 100 clients dont 11 souscrivent. Répondre « non » pour tout le monde donne 89 bonnes réponses, mais aucune information pour choisir les personnes à appeler. C'est pourquoi nous mesurons la classe positive et le classement, pas seulement le nombre total de réponses correctes.

Les taux changent selon les périodes :

| Partition | Lignes | Souscriptions |
|---|---:|---:|
| Entraînement | 24 712 | 4,81 % |
| Calibration | 4 119 | 10,15 % |
| Validation | 4 119 | 11,99 % |
| Test final | 8 238 | 30,83 % |

Les taux des blocs finaux sont présentés après évaluation. Leur variation montre que « 11 % de oui » ne décrit pas toutes les périodes. Le modèle doit faire face à un changement réel de contexte.

## 4. Qualité des données : trois notions différentes

**NaN / valeur absente** : le bloc d'entraînement n'en contient pas au chargement. Cela ne signifie pas que toute l'information est connue.

**`unknown`** : une chaîne explicite indique une information inconnue. Sur l'entraînement, `default` en contient 6 845. Nous la gardons comme catégorie, plutôt que d'inventer une réponse « non ». Son interprétation et sa fréquence doivent être surveillées.

**`pdays=999`** : il s'agit d'un code d'absence de contact antérieur, pas d'un délai de 999 jours à utiliser tel quel. Nous créons `previously_contacted`, puis remplaçons le code par une valeur manquante pour le délai. L'imputation est ensuite ajustée uniquement sur le train du fold.

Le fichier contient **12 doublons exacts**, dont 7 dans le train initial. Sans identifiant, nous ne pouvons pas prouver qu'ils sont des erreurs. Le brut est conservé ; les doublons de prédicteurs déjà vus sont exclus d'un bloc d'évaluation ultérieur, sans utiliser la cible. Ce contrôle ne suffit pas à détecter tous les contacts répétés d'une même personne.

## 5. Le piège central : `duration`

Pour décider qui appeler, nous sommes **avant l'appel**. La durée de cet appel n'est connue **qu'après**. Un modèle qui utilise `duration` bénéficie d'une information qu'il n'aura pas au moment réel de décider.

C'est une **fuite d'information**. Le problème n'est pas que la durée soit mathématiquement corrélée à la cible : une variable peut être très informative mais inutilisable pour la décision considérée.

Le sujet demande précisément de quantifier ce piège. Avec la même forêt de profondeur 8, l'AP moyenne de CV passe d'environ **0,495 avec duration** à **0,053 sans duration**. On compare ici le même modèle pour isoler le changement de variables.

À dire : « Le meilleur score apparent n'est pas forcément le meilleur modèle utilisable. La disponibilité des variables au moment de la décision fait partie de la validité du système. »

## 6. Pourquoi quatre scénarios ?

| Scénario | Ce qu'il conserve | Ce qu'il permet de comprendre |
|---|---|---|
| S1 | Toutes les variables | Référence diagnostique avec fuite |
| S2 | Toutes sauf duration | Impact du retrait de l'information future |
| S3 | S2 sans âge, profession, famille, éducation | Impact de la minimisation des variables discutables |
| S4 | Situation bancaire et cinq indicateurs macro | Faisabilité d'un modèle minimal, bonus du sujet |

S4 comporte **huit entrées**. Nous avons aussi retiré canal et date partielle pour avoir un modèle sans informations de campagne. Ce choix supplémentaire est documenté.

Retirer l'âge ne garantit pas l'équité : une autre variable peut être corrélée à l'âge. Il faut mesurer les erreurs par groupe même lorsque les variables de groupe ne servent plus à prédire. Nous conservons ces attributs dans la table d'audit, pas dans l'interface du modèle S4.

## 7. Séparer les rôles des données

Nous conservons l'ordre original et découpons en **60 % entraînement, 10 % calibration, 10 % validation, 20 % test**.

- Le train ajuste les modèles et contient la validation croisée.
- Le bloc calibration ajuste un éventuel correcteur de probabilité.
- La validation décide de conserver ou non cette correction et règle le seuil.
- Le test mesure le résultat final après gel des choix.

La **validation croisée temporelle** entraîne sur le passé puis évalue sur un bloc suivant. Trois fenêtres croissantes sont utilisées. Un écart de 100 lignes sépare train et validation des folds ; il s'agit de lignes, pas de jours. L'absence de timestamps complets et d'identifiants empêche des garanties plus fortes.

Un split aléatoire peut mélanger les contextes économiques. Nous le calculons seulement comme sensibilité dans le train initial : son AP moyenne d'environ **0,099** est plus favorable que l'AP temporelle d'environ **0,054**. Ce n'est pas le résultat principal.

Le test a été ouvert **une seule fois pour l'évaluation finale**. Les graphiques relisent les prédictions stockées. Le contrôle global initial du fichier avait déjà révélé les comptes de classes ; cette inspection préalable est déclarée.

## 8. Le pipeline : apprendre les transformations au bon endroit

Les nombres sont imputés puis standardisés. La standardisation soustrait une moyenne et divise par une échelle apprises sur le train ; elle aide notamment la régression logistique.

Les catégories sont imputées si nécessaire puis encodées en colonnes indicatrices avec **OneHotEncoder**. Une profession n'est pas transformée arbitrairement en un chiffre dont l'ordre signifierait « plus grand ». L'encodeur technique sait ignorer une catégorie non vue ; le service ajoute des contrôles explicites de domaine.

Ces transformations et le modèle sont réunis dans un **Pipeline**. Dans chaque fold, ils sont réajustés seulement sur la partie d'entraînement. Si l'on calculait les médianes ou l'encodage à partir de tout le fichier avant la CV, de l'information de validation entrerait dans la préparation.

Le pipeline complet est enregistré dans joblib. L'API recharge exactement les mêmes transformations que celles du modèle, évitant un décalage entre notebook et service.

À ouvrir : `src/bank_marketing/modeling/core.py`.

## 9. Les modèles comparés et le choix

**DummyClassifier** prédit la fréquence positive d'entraînement. Il vérifie si une méthode plus complexe apporte réellement quelque chose.

**Régression logistique** combine les variables dans une relation additive pour estimer une probabilité. Nous testons C=0,1 et C=1 ; C contrôle l'inverse de la régularisation. Ce n'est pas une régression de la cible numérique : ici elle sert bien à classer deux états.

**Forêt aléatoire** agrège 100 arbres. Nous comparons profondeur 8 / minimum 10 observations par feuille et profondeur 16 / minimum 5. Plus de profondeur peut représenter davantage de relations, mais augmente aussi la complexité et le risque de surajustement.

Au total : **4 scénarios × 5 configurations × 3 folds = 60 ajustements**. Pas besoin de LLM ni de RAG : il n'y a ni texte à générer, ni documents à rechercher. Le choix d'une famille est justifié par la tâche et les données.

La règle initiale exclut S1, puis préfère le plus petit périmètre parmi les configurations à moins de 0,02 AP du meilleur candidat. Elle retient **S4, forêt profondeur 8**. Cette règle privilégie fortement la minimisation lorsque tous les scores sont faibles : c'est une limite à expliquer, pas une raison de présenter le candidat comme excellent.

## 10. Comprendre chaque métrique avec nos résultats

Une matrice de confusion comporte quatre cases :

| | Réel non | Réel oui |
|---|---:|---:|
| Prédit non | TN = 2 352 | FN = 280 |
| Prédit oui | FP = 3 346 | TP = 2 260 |

Ces résultats utilisent le seuil de **0,05**, choisi sur validation, avant le filtre d'abstention.

- **Précision = TP/(TP+FP) = 40,31 %** : parmi les profils classés positifs, quatre sur dix ont souscrit historiquement.
- **Rappel = TP/(TP+FN) = 88,98 %** : presque neuf souscripteurs sur dix sont repérés.
- **F1 = 55,49 %** : compromis entre précision et rappel.
- **Accuracy = 55,98 %** : plus faible que le modèle toujours non sur ce bloc, parce que nous classons beaucoup de profils positifs.
- **ROC-AUC = 0,694** : mesure du classement des positifs face aux négatifs, indépendante du seuil choisi.
- **AP = 0,443**, contre **0,308** pour un score constant sur ce bloc : mesure de classement pertinente pour la classe positive.
- **Brier = 0,224** : erreur quadratique des probabilités ; plus petit est meilleur.

**Seuil et budget ne sont pas la même chose.** Le seuil 0,05 sélectionne **68,05 %** du test. Si l'on dispose d'un budget de 20 % de contacts, on prend les 20 % de scores les plus élevés : leur précision est **44,05 %**, soit un lift **1,43×** par rapport aux 30,83 % du bloc. Ne pas prétendre que le seuil 0,05 limite les appels à 20 %.

L'intervalle bootstrap indicatif de l'AP est environ **[0,424 ; 0,460]**. Il ne couvre pas toute l'incertitude temporelle ou la répétition possible de clients.

## 11. Calibration : pourquoi avons-nous refusé une correction ?

Un score de 0,20 devrait correspondre à environ 20 % de souscriptions sur des cas comparables pour être bien calibré. Un modèle peut bien classer tout en donnant des probabilités mal calibrées.

Nous avons ajusté une correction sigmoid sur un bloc dédié. Elle améliore le Brier de validation, mais sa pente vaut environ **−0,505** : elle inverse le sens du classement. La règle initiale impose une pente positive ; nous rejetons donc la correction.

Ce résultat indique une instabilité entre périodes. Nous ne l'utilisons pas comme une astuce pour obtenir un meilleur chiffre. La validation du candidat reste faible : AP **0,108** contre prévalence **0,120**, ROC-AUC **0,445**. Il faut le dire avant de vanter les métriques finales.

## 12. Équité : ce que montrent réellement les sous-groupes

Sur le test, le taux de faux positifs varie approximativement de **52 % chez les 31–45 ans** à **97 % chez les plus de 60 ans**. Le taux de sélection varie aussi fortement. Ces différences subsistent alors que l'âge n'est pas une entrée S4.

Cela démontre qu'un retrait de variable n'efface pas automatiquement les effets indirects. Cela ne démontre pas, à lui seul, une discrimination causale : périodes, taux de base et contexte diffèrent. Les tableaux donnent effectifs et petits groupes pour éviter les conclusions excessives.

L'audit porte aussi sur profession, éducation et situation familiale. Une analyse de production devrait ajouter incertitudes, stabilité dans le temps, intersection de groupes lorsque les effectifs le permettent et revue avec les personnes concernées.

## 13. Pourquoi le service s'abstient-il sur tout le test ?

Le service vérifie que les entrées restent dans les plages apprises sur le train. Les indicateurs macroéconomiques changent tellement que **100 % des lignes du dernier bloc ont au moins une valeur hors plage**.

Le résultat est une **couverture de 0 %** : aucune décision du modèle n'est émise sur ce bloc avec cette politique. Les chiffres du §10 décrivent donc le modèle **avant ce filtre**. Ils ne décrivent pas un service qui aurait réellement pris 8 238 décisions.

Ce contrôle est simple et conservateur ; min/max ne constitue pas un détecteur OOD sophistiqué. Mais l'assouplir après lecture du test pour afficher une meilleure couverture reviendrait à déplacer les objectifs. Nous documentons l'échec, livrons le mécanisme et bloquons la promotion.

La prochaine itération doit employer des fenêtres d'entraînement plus récentes, des backtests glissants et un nouveau jeu final indépendant. Elle peut comparer plusieurs politiques OOD sur validation. Elle ne doit pas réutiliser indéfiniment ce test comme terrain d'optimisation.

À dire : « La décision professionnelle est de ne pas déployer ce candidat. Le système logiciel fonctionne, mais les preuves d'utilité stable et de couverture sont insuffisantes. »

## 14. Comment fonctionne l'API ?

Le conseiller saisit les huit variables du modèle. **Pydantic** contrôle la forme et les types ; le service refuse des champs inattendus comme duration, des catégories invalides ou des nombres non finis.

Si le profil est dans le domaine et assez éloigné du seuil, `/predict` renvoie une probabilité et une priorité indicative. Sinon il renvoie une abstention, les motifs et `human_review`. Un profil invalide donne HTTP 422 ; un profil valide mais inhabituel donne une réponse explicite d'abstention, pas une erreur serveur.

`/health` indique que le service et le modèle sont chargés. `/model` décrit le contrat. `/feedback` ajoute le résultat réellement observé à une prédiction identifiée par UUID. `/monitoring` affiche les agrégats et `/metrics` expose la télémétrie Prometheus.

Les requêtes sont tracées sans imprimer les profils ni les jetons dans les logs HTTP. Un magasin local restreint conserve les variables nécessaires, version et résultat pour l'audit, avec conservation technique limitée. En usage réel, TLS, identité d'entreprise, chiffrement et gestion des droits doivent être ajoutés à l'hébergement.

## 15. Comment éviter un mauvais réentraînement ?

Un retour ne modifie pas immédiatement le modèle. Il faut suffisamment de résultats observés, les deux classes, puis vérifier les performances. Notre règle d'alerte demande au moins 200 labels et une chute d'AP de plus de 0,05 par rapport à la référence.

La dérive des entrées (**data drift**) ne prouve pas à elle seule que le lien entre entrées et résultat a changé (**concept drift**). PSI sert à signaler un changement de distribution ; les résultats observés servent à vérifier les performances.

`/train` exige un jeton et un snapshot approuvé différent du fichier d'examen. Il entraîne un candidat séparé et expose un statut de job. Il ne remplace jamais le modèle chargé. Le script de comparaison champion/challenger peut évaluer deux modèles sur une fenêtre commune approuvée, avec contrôle de chevauchement exact des observations d'entraînement.

La CI/CD exécute tests, entraînement, évaluation et gates. La promotion nécessite une revue et un environnement d'approbation. Le déploiement prévu vérifie la santé du conteneur et restaure l'ancienne image si le nouveau service échoue. Ces fichiers sont fournis, mais le serveur réel n'est pas configuré et le candidat actuel est bloqué.

## 16. Éthique et réglementation : les distinctions à retenir

Les variables de profil et de situation bancaire peuvent être des données personnelles même sans nom. L'âge et le statut marital sont discutables pour le ciblage, mais ne sont pas automatiquement des catégories particulières de l'article 9. Ne pas employer « sensible » comme si le sens courant et le sens juridique étaient identiques.

Le score ne donne pas un droit de contact. Le contrôle du consentement ou d'une exception applicable appartient au SI métier. La documentation juridique est datée et sourcée dans `ETHIQUE_ET_CONFORMITE.md` ; il faut la présenter comme une analyse à valider avec le DPO, pas comme une certification juridique.

Les points concrets sont : finalité claire, données limitées, information des personnes, droits, conservation justifiée, contrôle des accès et revue d'impact. Ne pas prétendre que le simple retrait de quatre colonnes rend tout le système conforme.

## 17. Démonstration de cinq minutes

1. Ouvrir `notebooks/certification.ipynb` ou `reports/certification.html` : annoncer le besoin et la conclusion.
2. Montrer le graphique S1–S4 : expliquer duration et le protocole identique.
3. Montrer la matrice de confusion et distinguer seuil 0,05 / budget top 20 %.
4. Montrer le graphique de dérive puis la couverture nulle : justifier la non-promotion.
5. Lancer l'API et ouvrir `/docs`, puis Streamlit. Envoyer un profil historique compatible, puis une valeur économique hors plage : montrer l'abstention.
6. Ajouter un retour de démonstration en le signalant comme tel ; montrer le suivi et le fait qu'aucun modèle n'est remplacé automatiquement.

Si l'API ne démarre pas le jour de l'oral, le HTML, OpenAPI exporté et réponses de smoke test sont disponibles. Ne pas présenter un fichier d'exemple comme une requête live.

## 18. Proposition de plan pour quinze minutes

| Temps | Message |
|---|---|
| 0–2 min | Besoin, décision avant appel, cible |
| 2–4 min | Source, déséquilibre, qualité et disponibilité |
| 4–7 min | Protocole, pipelines, modèles et scénarios |
| 7–10 min | Résultats, dérive, équité et non-promotion |
| 10–13 min | API, monitoring, feedback, tests et CI/CD |
| 13–15 min | Limites, prochaine itération et recommandation |

La durée de quinze minutes vient du canevas ; suivre les consignes effectives de votre session si elles diffèrent.

## 19. Questions probables du jury

**Pourquoi ne pas utiliser toutes les données pour entraîner ?** Parce qu'il faut simuler des données futures inconnues pour évaluer la généralisation. Ici plusieurs blocs ont des rôles distincts.

**Pourquoi ne pas entraîner avec duration si le score est meilleur ?** Parce que la variable n'existe pas au moment où la décision doit être prise.

**Pourquoi S4 alors que son gain de CV est faible ?** La règle préétablie privilégie la minimisation près du meilleur score. Cela désigne un candidat technique, pas un modèle validé pour le métier ; la revue le rejette.

**Pourquoi ne pas annoncer seulement le test favorable ?** La validation et la couverture montrent une instabilité ; sélectionner les résultats favorables serait trompeur.

**Pourquoi pas de deep learning ?** Aucun besoin démontré sur ce volume tabulaire pour justifier complexité, coût et tuning supplémentaires.

**Supprimer l'âge résout-il les biais ?** Non : d'autres variables peuvent agir comme proxys, et les données historiques peuvent être biaisées.

**Comment prouver que le code marche ?** Tests automatisés des contrats, des transformations, de l'API et des gates ; smoke tests sur l'artefact réel ; notebook exécuté avec méthode indiquée.

**Est-ce en production ?** Non. Prototype local testé ; scripts de déploiement fournis ; aucune instance distante lancée et gates de production échoués.

**Que ferais-tu ensuite ?** Acquérir des données récentes et autorisées, évaluer par fenêtres glissantes, comparer champion/challenger, choisir les règles sur validation et préserver un nouveau test.

## 20. Ce qu'il faut vraiment savoir expliquer sans lire

Le lien besoin → disponibilité des variables → protocole → métriques → décision. La différence entre une API fonctionnelle et un modèle utile. Pourquoi le projet ne s'arrête pas à `fit()`, et pourquoi une non-promotion argumentée peut être un meilleur travail d'ingénierie qu'un déploiement injustifié.
