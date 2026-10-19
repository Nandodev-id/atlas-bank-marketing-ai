### 6.5 — Synthèse RGPD et AI Act

**Périmètre :** prioriser une campagne de dépôt à terme, sans évaluer la solvabilité, accorder un crédit ni autoriser automatiquement un contact. Une réutilisation pour le crédit exige une nouvelle analyse.

| Sujet | Décision de conception / condition avant usage réel |
|---|---|
| Finalité et base légale | Documenter séparément le développement et l'utilisation opérationnelle avec le DPO ; un CSV public ne donne pas automatiquement une base légale. |
| Minimisation | Écarter duration avant appel ; limiter les entrées. Le retrait des variables démographiques n'élimine pas les proxys et ne démontre pas l'équité. |
| Données personnelles | L'absence de noms ne suffit pas à démontrer l'anonymat. Âge/profession ne sont pas, à eux seuls, les catégories particulières de l'article 9 ; inférences et contexte doivent être examinés. |
| Droit de contact | Pour les consommateurs en France, consentement préalable au démarchage téléphonique depuis le 11 août 2026, sous réserve des exceptions légales, notamment relatives à un contrat en cours. Le CSV ne contient pas ces preuves : `contact_authorized=false`. |
| Droits et information | Informer sur le traitement/profilage ; organiser accès, rectification, effacement lorsque applicable et opposition à la prospection. Examiner l'article 22 si la décision automatisée produit des effets juridiques ou similaires significatifs. |
| Conservation et sécurité | Les 30 jours d'audit sont une hypothèse à valider, pas une obligation légale générale. Prévoir accès restreints, purge, TLS, sauvegardes et gestion des droits ; pas de profils dans les logs HTTP. |
| Responsabilités | Responsable de traitement, métier, SI et DPO doivent valider le dispositif ; évaluer le besoin d'AIPD avant usage réel. Le projet ne constitue pas une certification de conformité. |

Sources RGPD : [CNIL, principes et bases légales, articles 5–9](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre2), [droits et décisions automatisées, articles 13–22](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre3). Droit de contact : [CNIL, démarchage commercial](https://cnil.fr/fr/demarchage-commercial), [Code de la consommation, L223-1 et suivants](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006069565/LEGISCTA000032221441/). Sources consultées le 19 octobre 2026.

**AI Act : qualification par la finalité.** L'annexe III, point 5(b), vise notamment l'évaluation de la solvabilité ou l'établissement d'une note de crédit des personnes physiques. Ce n'est pas la finalité annoncée ici. Le seul fait d'être utilisé dans une banque ne suffit donc pas à classer ce projet dans cette catégorie à haut risque. Il faut néanmoins examiner l'ensemble des critères applicables de l'article 6 et de l'annexe III, les pratiques interdites et les obligations pertinentes pour le déploiement réel. La qualification proposée reste à valider avec la conformité. Source primaire : [règlement (UE) 2024/1689, article 6 et annexe III](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ%3AL_202401689).

**Décision actuelle : aucune campagne réelle avec ce candidat.** La qualité insuffisante, l'absence de couverture et les écarts entre groupes suffisent à bloquer sa promotion, indépendamment de sa qualification réglementaire.
