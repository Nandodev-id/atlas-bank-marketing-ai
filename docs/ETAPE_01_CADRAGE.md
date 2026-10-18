> Historique de la première étape, conservé pour traçabilité. Pour l’état final, lire le README, le notebook de certification et `COUVERTURE_EXAMEN.md`.

## 1. Cadrage métier & problème

**Compétences : C1, C2, C4. Étape 1 — proposition de cadrage à expliquer à l'oral.**

### 1.1 Contexte client
Une banque de détail souhaite mieux cibler ses appels proposant un dépôt à terme. Les appels mobilisent les conseillers et peuvent importuner les clients. Le modèle aidera le responsable de campagne à prioriser les contacts ; il ne décide pas de l'accès à un crédit. Le fichier fourni décrit des contacts historiques d'une banque portugaise : ce n'est pas une preuve de performance sur une banque actuelle.

### 1.2 Énoncé du problème IA
Estimer la probabilité de souscription (`y=yes`) à partir des informations disponibles **avant l'appel à planifier**. C'est une classification binaire supervisée : les exemples historiques portent déjà la réponse `yes` ou `no`.

`duration` est connue après l'appel : elle est exclue des modèles utilisables avant appel. Le scénario S1 la conserve uniquement pour illustrer cette fuite d'information. Il faut aussi vérifier la disponibilité de `campaign` (qui inclut le contact courant), du canal, de la date prévue et des indicateurs économiques à la date de décision. Retirer `duration` ne suffit pas à prouver que toutes les autres variables sont utilisables.

### 1.3 Bénéficiaires & impacts
- Utilisateurs directs : responsables de campagne et conseillers.
- Personnes concernées : clients contactés ou non retenus dans la liste prioritaire.
- Parties à consulter : métier (budget d'appels), SI (intégration), DPO/conformité (usage des données).
- Faux positif : on priorise un client qui ne souscrit pas, donc un appel potentiellement inutile.
- Faux négatif : on ne priorise pas un client qui aurait souscrit dans les conditions historiques observées.

Le modèle estime une association dans les données observées, pas l'effet causal d'un appel. Une amélioration réelle du taux de conversion devra être vérifiée sur le terrain.

### 1.4 Critères de succès
Le sujet ne fournit ni budget d'appels, ni coût par appel, ni gain par souscription, ni seuil chiffré contractuel. Les objectifs suivants sont des propositions de travail, pas des exigences inventées du client. Les seuils seront figés avant l'évaluation finale.

| Type | Critère | Cible initiale | Révision après EDA |
|---|---|---|---|
| Métier | Souscriptions identifiées pour un budget de contacts donné | Faire mieux qu'une sélection aléatoire à budget identique ; budget à préciser | À documenter sur les données de développement |
| Modèle | Précision, rappel, F1 de la classe oui, ROC-AUC, matrice de confusion ; AP pour le classement | Comparer DummyClassifier, régression logistique et forêt aléatoire | Choisir métrique et seuil sur validation, jamais sur test final |
| Opérationnel | Latence p95, erreurs, validation des entrées | Hypothèse initiale : p95 < 500 ms en local, conditions de mesure à préciser | À mesurer, aucune performance annoncée à ce stade |
| Responsable | Écarts de sélection et d'erreurs entre sous-groupes | Mesurer et expliquer les écarts ; seuils à justifier | À documenter avec effectifs par groupe |

Le contrôle initial du fichier a trouvé 4 640 oui sur 41 188 lignes (11,27 %). Prédire toujours non donnerait 88,73 % d'accuracy et un rappel de 0 % pour les souscriptions. Ce contrôle global est déjà connu ; le protocole de test final n'est pas encore défini. Nous n'affirmons pas disposer à ce stade d'un test entièrement vierge de toute inspection.

### 1.5 Risques éthiques & réglementaires anticipés
Risques à instruire : ciblage inéquitable lié à l'âge, la profession, la situation familiale ou l'éducation ; variables indirectes qui reproduisent ces informations ; sollicitations excessives ; conservation et exposition inutiles de données dans les journaux.

L'examen demande de distinguer données personnelles, catégories particulières de l'article 9, et variables éthiquement discutables. Cette analyse juridique reste à rédiger à partir de sources officielles actualisées, avec une base légale et des durées de conservation à valider par le DPO. Le retrait des variables discutables ne prouve pas à lui seul l'équité.

### 1.6 Synthèse cadrage
Nous aidons la banque à prioriser ses contacts pour un dépôt à terme grâce à une classification binaire. La décision intervient avant l'appel : sa durée n'est donc pas utilisable. Le succès se jugera sur l'utilité à budget de contacts donné, les erreurs sur les souscripteurs et les écarts entre groupes. Aucun modèle ni gain métier n'est encore validé.

## À expliquer au jury en 45 secondes
« Mon projet aide une banque à prioriser les clients à appeler pour proposer un dépôt à terme. J'utilise une classification binaire pour estimer la probabilité de souscription. Comme seulement 11 % des observations sont positives, une bonne accuracy ne suffit pas. Je compare plusieurs modèles et plusieurs jeux de variables, en retirant notamment la durée de l'appel, inconnue au moment de décider qui appeler. Mon choix final devra concilier performance, équité et conditions de déploiement. »

## Vérification de compréhension
1. Que représente `y` ?
2. Pourquoi 89 % d'accuracy peut-il correspondre à un modèle inutile ?
3. Pourquoi `duration` crée-t-elle une fuite d'information ?
4. Quelle différence entre un faux positif et un faux négatif ici ?
5. Pourquoi retirer l'âge ne garantit-il pas l'absence de biais ?

Réponses : `y` est la souscription ; toujours prédire non ignore tous les souscripteurs ; la durée est connue après la décision ; faux positif = contact priorisé sans souscription, faux négatif = souscripteur non repéré ; d'autres variables peuvent servir de proxys et les erreurs doivent être mesurées par groupe.
