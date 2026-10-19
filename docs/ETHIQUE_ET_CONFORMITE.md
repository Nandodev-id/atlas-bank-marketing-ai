# Éthique et conformité — analyse pédagogique, 18 octobre 2026

## Finalité et périmètre

Le service estime une propension à souscrire un dépôt à terme. Il n'évalue pas la solvabilité et n'accorde ni ne refuse de crédit. Une éventuelle réutilisation en scoring de crédit changerait la finalité et imposerait une nouvelle analyse. Les résultats historiques portugais (2008–2010) ne permettent aucune conclusion automatique sur une banque française actuelle.

## Nature des données

Âge, profession, situation familiale, éducation, situation bancaire et historique de contacts peuvent être des données personnelles lorsqu'ils se rapportent à une personne identifiable. L'absence de nom ne prouve pas l'anonymisation : une combinaison de caractéristiques peut permettre un rapprochement. Les indicateurs macroéconomiques décrivent le contexte, mais le fichier joint reste un fichier de profils.

Aucune colonne ne décrit explicitement une catégorie particulière de l'article 9. L'âge ou le statut marital peuvent être éthiquement discutables sans relever, à eux seuls, de cet article. Les inférences et proxys restent à examiner. Le choix S3 retire âge, profession, situation familiale et éducation pour réduire les risques de ciblage social ; S4 minimise davantage. Aucun retrait ne démontre l'équité. [RGPD, articles 5, 6 et 9 — CNIL](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre2).

## Base légale et droit de contact

Le consentement peut fonder le traitement ; l'intérêt légitime demande une analyse de nécessité et de mise en balance documentée. Une base légale ne se déduit pas de la disponibilité publique du CSV. La base du développement et celle de l'utilisation opérationnelle doivent être instruites séparément avec le DPO. [CNIL : définir une base légale](https://www.cnil.fr/fr/assurer-que-le-traitement-est-licite).

En France, depuis le 11 août 2026, le démarchage téléphonique des consommateurs exige un consentement préalable, sauf exception liée à un contrat en cours dans les conditions applicables. Ne pas assimiler « client existant » à une permission générale. Le SI devra vérifier l'éligibilité, la preuve de consentement ou l'exception, et les oppositions **avant** de transmettre un contact à la campagne. Le CSV ne contient pas ces preuves. L'API renvoie donc `contact_authorized=false`. [CNIL : démarchage commercial](https://cnil.fr/fr/demarchage-commercial).

## Information, droits et sécurité

Informer sur la finalité et le profilage ; organiser accès, rectification, opposition et effacement lorsque applicables. L'opposition à la prospection doit être prise en compte. Un classement assisté n'autorise pas à ignorer l'encadrement des décisions automatisées produisant des effets significatifs. [RGPD, articles 13–22 — CNIL](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre3).

Le prototype conserve uniquement les variables du modèle, un identifiant aléatoire, la version, le score et éventuellement le résultat observé dans SQLite, avec permissions locales 0600. Les logs HTTP ne contiennent ni corps de requête ni jeton. La conservation technique de 30 jours est une **hypothèse configurable à valider**, pas une durée légale universelle ; l'effacement intervient lors des accès au magasin. Une tâche de purge planifiée reste nécessaire sur un serveur inactif. Chiffrement du disque, TLS, sauvegardes, contrôle des accès, rotation de secrets et gestion des droits doivent être configurés sur l'hébergement réel. Le jeton partagé de démonstration devra être remplacé par l'identité d'entreprise et des rôles.

## Équité et décision

Les tableaux `fairness_validation.csv` et `fairness_test.csv` présentent effectifs, sélection, faux positifs et faux négatifs par âge, profession, situation familiale et éducation. Les petits groupes sont marqués. Ces différences sont descriptives, liées aussi à des taux de base et contextes différents ; elles ne suffisent pas à établir une discrimination causale.

Malgré le retrait des variables socio-démographiques, des écarts importants subsistent. La décision est de ne pas promouvoir le candidat. Une prochaine itération doit tester des données récentes, des fenêtres glissantes et la stabilité par groupe ; elle doit disposer d'un nouveau test indépendant. L'évaluation des risques et, si nécessaire, une AIPD précèdent tout usage réel. [CNIL : analyse d'impact](https://cnil.fr/fr/realiser-une-analyse-dimpact-si-necessaire).

## AI Act

Ne pas qualifier automatiquement tout système bancaire de « haut risque ». La finalité précise, le contexte d'utilisation et les dispositions applicables doivent être analysés. Ce projet de marketing n'est pas présenté comme une évaluation de solvabilité. Nous ne certifions aucune conformité AI Act ; la qualification et les obligations exactes restent une responsabilité de conformité avant usage réel.

## Décision opérationnelle — revue du 19 octobre 2026

Le taux de sélection de 98,44 % des plus de 60 ans et leur FPR de 97,08 % sont calculés avant le filtre d'abstention, qui rejette tout le test. La décision reste le blocage de toute campagne fondée sur ce candidat. Les responsables, contrôles et conditions de réexamen sont précisés dans `DECISION_EQUITE.md` et intégrés à la section 6.4 du notebook ; la section 6.5 reprend la synthèse réglementaire et ses sources primaires.
