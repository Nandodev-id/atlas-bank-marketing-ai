## 1. Cadrage métier & problème

**Compétences : C1, C2, C4.**

### 1.1 Contexte client
Une banque souhaite prioriser les appels proposant un dépôt à terme pour limiter les sollicitations inutiles et le temps des conseillers. La source décrit des campagnes historiques d'une banque portugaise ; elle ne démontre pas une performance sur une banque actuelle. Le système n'accorde ni ne refuse un crédit.

### 1.2 Énoncé du problème IA
Estimer la probabilité `y=yes` à partir d'informations connues **avant l'appel à planifier**. Classification binaire supervisée : les observations d'entraînement ont déjà leur réponse yes/no.

`duration` est connue après l'appel, donc exclue de tout modèle utilisable en amont. S1 la conserve seulement pour mesurer la fuite. Pour S2/S3, `campaign` doit représenter le rang de l'appel prévu, `contact` le canal prévu, et mois/jour la date prévue ; il faut vérifier les dates de publication des indicateurs macroéconomiques. S4 retire les variables de campagne, mais reste dépendant d'indicateurs économiques disponibles à temps.

### 1.3 Bénéficiaires & impacts
Les responsables de campagne et conseillers sont les utilisateurs directs ; les clients subissent la sélection et les sollicitations. Le métier valide le budget et les coûts, le SI l'intégration, et le DPO/conformité l'usage des données et les conditions de contact.

Un faux positif est un contact priorisé qui ne souscrit pas. Un faux négatif est un souscripteur historique non repéré. Le score prédit une association, pas l'effet causal d'un appel : un gain métier réel exige une évaluation terrain contrôlée.

### 1.4 Critères de succès
Le sujet ne donne ni coût d'appel, ni gain par souscription, ni budget contractualisé. Nous annonçons des hypothèses, pas des objectifs attribués au client.

| Type | Cible initiale proposée | Révision / résultat |
|---|---|---|
| Métier | Faire mieux qu'une sélection aléatoire à budget identique ; budget illustratif de 20 % | Lift test 1,43×, mais validation 0,82× : utilité stable non démontrée, aucun ROI monétaire annoncé |
| Modèle | Comparer Dummy, LogReg et forêt avec AP, précision, rappel, F1, AUC et confusion | AP finale 0,443 ; AP de validation 0,108 sous sa prévalence : résultat insuffisant pour promouvoir |
| Opérationnel | Hypothèse p95 < 500 ms | Satisfait dans les mesures locales séquentielles ; charge et réseau non évalués |
| Responsable | Mesurer les différences entre groupes et limiter le ciblage injustifié | Écarts persistants, couverture du service nulle sur le test ; revue et nouvelles données requises |

Les cibles ne sont pas modifiées après le test pour déclarer une réussite. La revue de production ajoute des seuils pédagogiques de couverture/écarts, explicitement identifiés comme postérieurs dans le journal. Le protocole de sélection reste inchangé.

Le fichier global contient 11,27 % de souscriptions ; toujours répondre non donne 88,73 % d'accuracy et 0 % de rappel. Ce contrôle global a précédé le protocole et est déclaré.

### 1.5 Risques éthiques & réglementaires anticipés
Risques : ciblage lié au profil social, proxys indirects, excès de sollicitations, exposition des profils dans les logs, obsolescence de la source. Les variables éthiquement discutables ne sont pas automatiquement des catégories particulières de l'article 9. La base légale, l'information, les droits et la conservation doivent être validés avec le DPO ; l'analyse documentée se trouve dans `docs/ETHIQUE_ET_CONFORMITE.md`.

Le système ne possède pas de preuve de consentement au contact. Il renvoie `contact_authorized=false`. Retirer quatre variables n'établit ni équité ni conformité générale.

### 1.6 Synthèse cadrage
Nous cherchons une aide à la priorisation avant appel, avec minimisation des données et mesure des erreurs. Le pipeline et le service sont exécutables, mais le candidat n'est pas promouvable : validation instable, écarts par groupe et couverture nulle sur le bloc final. Cette conclusion distingue la livraison technique d'une autorisation d'usage réel.
