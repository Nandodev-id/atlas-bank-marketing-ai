### 6.4 — Équité : décision opérationnelle et conditions de réexamen

Les tableaux de la première évaluation décrivent le **modèle avant abstention**, pas des décisions effectivement émises par l'API. Le service s'abstient sur tout le test.

Chez les plus de 60 ans : **767 observations, 755 profils sélectionnés, soit 98,44 %** ; 399 faux positifs parmi 411 non-souscripteurs, soit **97,08 % de FPR**. La prévalence de souscription est de 46,41 %. Le taux de sélection des 31–45 ans est de 60,76 %. Ces différences nécessitent une investigation ; elles ne démontrent pas à elles seules une discrimination causale. Les données décrivent des clients historiquement contactés et ne permettent pas d'estimer l'effet causal d'une nouvelle campagne.

**Décision : ne pas promouvoir le modèle et ne lancer aucune campagne sur ce score.** On ne compense pas le problème en choisissant après coup un seuil spécifique aux seniors sur ce test. Le retrait de l'âge des entrées n'a pas suffi à éliminer les écarts.

Avant de réexaminer la décision :

1. **Métier et DPO** définissent la finalité, les groupes à auditer, le coût des sollicitations inutiles et les critères d'acceptation, avant les nouvelles expériences. Les seuils pédagogiques actuels ne sont pas des normes légales.
2. **Équipe données** collecte un échantillon récent et représentatif avec permissions de contact et résultats observés ; elle examine les proxys, les taux de base et les contacts répétés. Elle n'interprète pas l'absence de retour comme une non-souscription.
3. **Équipe ML** mène des backtests temporels, mesure sélection, FPR/FNR, calibration et couverture par groupe avec effectifs et incertitudes. Elle évalue sur un nouveau test réservé. Une bonne métrique globale ne suffit pas à accepter de forts écarts non expliqués.
4. **Métier, SI et DPO** documentent l'acceptation ou le refus avant tout pilote contrôlé. Une revue humaine ne rend pas automatiquement acceptable un modèle défaillant ; le score actuel reste hors campagne.
