"""Fill every official canvas section with executed evidence and reasoned decisions."""

import json
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "reports"
read = lambda name: json.loads((R / name).read_text())
s = read("selection.json")
f = read("final_test.json")
a = read("data_audit.json")
p = read("production_decision.json")
n = nbf.read(ROOT / "cas_usage_certif/canvas-cas-usage-v2.ipynb", as_version=4)


def md(i, text):
    n.cells[i] = nbf.v4.new_markdown_cell(text)


def code(i, text):
    n.cells[i] = nbf.v4.new_code_cell(text)


md(
    0,
    """# Cas d'usage IA — Atlas : marketing bancaire responsable

**Auteur : Fernando** · Dev-id · Certification CISIA C1–C9 / OPCO Atlas  
**Expérience de référence : 18 octobre 2026**

Ce cahier suit le canevas officiel `cas_usage_certif/canvas-cas-usage-v2.ipynb`, conservé sans adaptation dans le dossier `cas_usage_certif/`. Il réunit le raisonnement, les preuves et le journal de bord. Le code du service reste dans le dépôt.

**Conclusion : projet pédagogique exécuté, candidat non promouvable en production.** Le modèle classe mieux que le hasard sur le dernier bloc, mais sa validation temporelle est faible, les écarts entre groupes persistent et le service s'abstient sur tout le test final. Cette conclusion fait partie du résultat, elle n'est pas masquée.

Les cellules relisent les artefacts issus d'une expérience réelle et figée. Elles ne réentraînent pas silencieusement le modèle à chaque lecture. Pour reproduire depuis zéro : commandes en section 5.2 et README. Les figures sont incorporées aux sorties pour une lecture portable du `.ipynb`.""",
)
md(
    2,
    """## Mobilisation du canevas et parcours de lecture

Toutes les sections 0 à 9 sont mobilisées pour ce cas de certification. Lire d'abord le besoin (§1), les données (§2–3), le protocole (§4), les résultats (§5–6), puis la recommandation et le service (§7–9). Chaque section termine par une synthèse. Les modules de code se trouvent dans `src/bank_marketing`, les tests dans `tests`, les preuves dans `reports`.

**Distinction importante** : un modèle entraîné, une API testée et une mise en production autorisée sont trois états différents. Nous avons les deux premiers, pas le troisième.""",
)
code(
    4,
    """# Tous les imports et la configuration sont centralisés ici.
import hashlib
import inspect
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from IPython.display import Code, Image, Markdown, display
from bank_marketing.modeling import core, train as training_module
from bank_marketing.monitoring.checks import retraining_decision

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
pd.set_option('display.max_columns', 30)
sns.set_theme(style='whitegrid')
ROOT = Path.cwd() if (Path.cwd() / 'pyproject.toml').exists() else Path.cwd().parent
REPORTS = ROOT / 'reports'
ARTIFACTS = ROOT / 'artifacts'

def read_report(name):
    return json.loads((REPORTS / name).read_text())

def figure(name):
    display(Image(filename=str(REPORTS / 'figures' / name)))

selection = read_report('selection.json')
final = read_report('final_test.json')
metadata = read_report('metadata.json')
audit = read_report('data_audit.json')
protocol = read_report('protocol.json')
production = read_report('production_decision.json')
cv_results = pd.read_csv(REPORTS / 'cv_comparison.csv')
print('Racine du projet :', ROOT)
""",
)
code(
    6,
    """# Empreinte de la source, environnement réellement utilisé et version du code.
source = ROOT / 'data/raw/bank-additional-full.csv'
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash == metadata['data_sha256']
print('Python du notebook :', platform.python_version())
print('Dataset : UCI Bank Marketing, variante bank-additional-full')
print('SHA-256 :', source_hash)
print('Commit lors de l’entraînement :', metadata['git_commit'])
print('Modifications locales présentes lors de l’entraînement :', metadata['git_dirty'])
display(pd.Series(read_report('environment.json')['packages'], name='Version testée').to_frame())
print('L’environnement complet est archivé dans reports/environment_all_packages.json.')
""",
)
md(7, (ROOT / "docs/CADRAGE_FINAL.md").read_text())
md(
    9,
    """### 2.1 Sources

| Source | Type / volumétrie | Accès et date | Traçabilité |
|---|---|---|---|
| CSV fourni avec le sujet | 41 188 lignes, 20 prédicteurs + `y`, séparateur `;` | Lecture locale, contrôlé le 18/10/2026 ; date d'extraction initiale inconnue | SHA-256 ci-dessus |
| Sujet d'examen | PDF, 6 pages | Fourni par l'apprenant | Dictionnaire et obligations S1–S3 |
| UCI Bank Marketing | Banque portugaise, observations mai 2008–novembre 2010 | Source officielle vérifiée | [UCI](https://archive.ics.uci.edu/dataset/222/bank+marketing) ; licence CC BY 4.0 |

UCI regroupe plusieurs variantes. Les 45 211 lignes affichées dans l'en-tête de sa page concernent une autre variante : notre fichier est bien **bank-additional-full**, 41 188 lignes et 20 entrées. UCI confirme son ordre par date ; nous conservons l'ordre des lignes, sans prétendre reconstruire des dates exactes ni des identifiants client.

Citation : Moro, S., Rita, P., & Cortez, P. (2014), *Bank Marketing*, UCI, DOI 10.24432/C5K306. La licence du dataset ne dispense pas d'analyser la licéité d'un usage réel de données personnelles.""",
)
code(
    10,
    """# 2.2 Chargement et séparation selon les indices figés avant modélisation.
df = pd.read_csv(source, sep=';')
split_indices = json.loads((ARTIFACTS / 'split_indices.json').read_text())
train_df = df.loc[split_indices['train']].copy()
calibration_df = df.loc[split_indices['calibration']].copy()
validation_df = df.loc[split_indices['validation']].copy()
# Le test a déjà été ouvert une fois par le script final, après gel des choix.
print('Forme source :', df.shape)
display(pd.DataFrame({'lignes': {k: len(v) for k, v in split_indices.items()}}))
""",
)
dictionary = """| Variable | Signification et valeurs | Type | Disponibilité / vigilance |
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
| y | Dépôt souscrit : yes/no | cible binaire | Résultat futur, jamais une entrée du modèle |"""
(ROOT / "docs/DICTIONNAIRE_DONNEES.md").write_text(
    "# Dictionnaire du sujet\n\n" + dictionary + "\n"
)
md(
    11,
    "### 2.3 Dictionnaire de variables\n\n"
    + dictionary
    + """

### 2.4 Synthèse acquisition
Le fichier fourni est intègre et correspond à la variante attendue. Il contient des informations de profil, de contact et de contexte économique. L'ordre temporel est documenté, mais les identifiants client et timestamps complets manquent ; nous ne pouvons donc pas garantir l'indépendance des personnes entre partitions.
""",
)
code(
    13,
    """# 3.1 Explorer uniquement le bloc d'entraînement pour guider les choix.
display(train_df.head())
train_df.info()
display(train_df.describe(include='all').T)
""",
)
code(
    14,
    """# 3.2 Ne pas confondre NaN, unknown et code sentinelle.
display(pd.DataFrame({'NaN': train_df.isna().sum(),
                      'unknown': (train_df == 'unknown').sum()}))
print('Doublons exacts entraînement :', train_df.duplicated().sum())
print('pdays=999 entraînement :', (train_df.pdays == 999).sum())
figure('unknown.png')
""",
)
code(
    15,
    """# 3.3 Chaque figure répond à une question : asymétrie, extrêmes, échelle.
figure('distributions.png')
print('Les valeurs extrêmes ne sont pas supprimées automatiquement : elles peuvent être légitimes.')
""",
)
code(
    16,
    """# 3.3 bis : cas exclusivement tabulaire. Pas de texte libre, image ou audio.
print('Aucune modalité non tabulaire à vectoriser ; pas de justification pour NLP/RAG.')
""",
)
code(
    17,
    """# 3.4 Pourquoi l'accuracy seule est trompeuse.
figure('target.png')
rate = (train_df.y == 'yes').mean()
print(f'Prévalence entraînement : {rate:.2%}')
print(f'Toujours non : accuracy={1-rate:.2%}, rappel des souscriptions=0 %')
""",
)
code(
    18,
    """# 3.5 Les variables économiques peuvent être redondantes.
figure('correlations.png')
# Constat final, présenté explicitement après l'évaluation déjà réalisée.
figure('time_shift.png')
""",
)
md(
    19,
    """### 3.6 Analyse des biais & variables sensibles

Les profils historiques représentent des personnes déjà contactées, pas tous les clients potentiels. C'est un biais de sélection ; les non-contactés ne disposent pas d'un résultat comparable. Des appels répétés peuvent concerner une même personne, sans identifiant permettant un découpage par client.

Âge, profession, statut marital et éducation sont retirés en S3/S4 pour minimiser le ciblage social direct. Les variables économiques et bancaires peuvent encore être des proxys. Mesurer sélection, FPR et FNR par groupe reste nécessaire après retrait. Les mesures finales sont en §6–7 ; les groupes avec moins de 100 observations ou moins de 20 cas d'une classe sont signalés.

Une différence de taux n'est pas une preuve causale de discrimination ; l'absence de différence observée ne prouverait pas l'équité non plus.""",
)
md(
    20,
    f"""### 3.7 Synthèse EDA

1. Aucune valeur NaN dans le bloc d'entraînement, mais de nombreux `unknown` : ce sont des valeurs métier explicites conservées comme modalités.
2. `pdays=999` concerne {a['train_pdays_999']:,} lignes d'entraînement sur {a['train_rows']:,} : séparer absence d'historique et délai réel.
3. Prévalence d'entraînement {a['split_prevalence']['train']:.2%}, très inférieure aux {a['split_prevalence']['test']:.2%} du test constatés après ouverture : fort changement temporel.
4. Doublons et absence d'identifiant imposent de documenter le risque de répétition plutôt que supprimer à l'aveugle.
5. `duration` est une fuite pour décider avant l'appel ; les variables macroéconomiques ont une forte dépendance au temps. Ces constats justifient comparaison de scénarios et évaluation ordonnée.
""",
)
code(
    22,
    """# 4.1 Protocole figé avant ouverture du test : 60/10/10/20.
display(pd.Series(protocol, name='Décision').to_frame())
for left, right in [('train', 'calibration'), ('calibration', 'validation'), ('validation', 'test')]:
    assert max(split_indices[left]) < min(split_indices[right])
    assert not set(split_indices[left]) & set(split_indices[right])
print('Ordre et disjonction vérifiés. Gap CV = 100 lignes, pas 100 jours.')
print('CV : 3 fenêtres croissantes sur les 60 % initiaux seulement.')
print('Les doublons exacts de prédicteurs déjà vus sont purgés des blocs ultérieurs sans lire y.')
""",
)
code(
    23,
    """# 4.2 Recette commune et transformation sérialisable : aucun fit ici.
display(Code(inspect.getsource(core.FeatureBuilder), language='python'))
display(Code(inspect.getsource(core.make_pipeline), language='python'))
""",
)
md(
    24,
    """### 4.3 Scénarios de jeux de données

| Scénario | Variables | Rôle |
|---|---|---|
| S1 | Les 20 variables, dont duration | Illustration de fuite, jamais déployable |
| S2 | 19 variables sans duration | Mesurer le coût de retrait de la fuite |
| S3 | S2 sans age, job, marital, education : 15 variables | Minimisation des variables discutables |
| S4 | S3 sans historique ni canal/date de campagne : 8 variables | Bonus minimal : default, housing, loan et 5 indicateurs économiques |

Les scénarios du **PDF** priment sur les noms d'exemples génériques du canevas. Un facteur est modifié à la fois : même modèle comparé entre scénarios, puis mêmes variables entre modèles. Imputation, normalisation et encodage suivent la même recette dans chaque fold ; seuls les périmètres changent. `pdays=999` est remplacé par NaN et complété par un indicateur avant l'imputation ; cette transformation est déterministe. Les médianes et modalités sont apprises sur le train du fold.

### 4.4 Synthèse préparation
Le test final reste à la fin de la source ordonnée. La validation sert au seuil et au contrôle de calibration, jamais au score final annoncé. Aucun SMOTE n'est appliqué : la priorité est une comparaison lisible des probabilités et du classement ; un éventuel rééquilibrage devrait être testé dans les folds, pas avant le split.""",
)
code(
    26,
    """# 4.5 Assertions de qualité réellement exécutées.
assert df.shape == (41188, 21)
assert set(df.y.unique()) == {'yes', 'no'}
assert source_hash == '74adfc578bf77a7ff4bb1ba4a9f8709d9e3c6907342959c2c8416847e0afb4d8'
feature_sets = core.scenarios(df.columns)
assert 'duration' not in feature_sets['S2']
assert not set(core.SENSITIVE) & set(feature_sets['S3'])
assert len(feature_sets['S4']) == 8
assert all('y' not in features for features in feature_sets.values())
print('Contrat source, cible, scénarios et séparation vérifiés.')
""",
)
md(
    28,
    """### 5.0 Familles de modèles candidates

| Famille | Adaptation / coût | Explicabilité et dépendance | Arbitrage |
|---|---|---|---|
| ML classique | Données structurées, 41k lignes, CPU raisonnable | Régression lisible ; arbres inspectables ; exécution locale | Retenue |
| Deep Learning | Possible mais complexité et tuning supplémentaires sans besoin démontré | Explication plus délicate ; bibliothèque locale possible | Écarté pour cette première comparaison |
| SLM local | Génération de texte non demandée | Maintenance et ressources supplémentaires | Écarté : pas de tâche linguistique |
| LLM API + RAG | Aucun corpus documentaire à interroger | Coût externe et transfert de données inutiles ici | Écarté |
| Architecture agentique | Aucune orchestration décisionnelle multi-outils requise | Coût et risques d'action supplémentaires | Écartée |

### 5.0.1 Synthèse familles
Le besoin est une classification tabulaire. Le choix ML classique repose sur la structure des données, le coût CPU et l'auditabilité, pas sur une préférence personnelle pour un outil. Aucune supériorité quantitative du ML sur des familles non testées n'est inventée.""",
)
md(
    29,
    """### 5.1 Modèles candidats

| Modèle | Réglages testés | Intérêt | Limite |
|---|---|---|---|
| DummyClassifier prior | Fréquence de la classe positive | Point de comparaison sans apprentissage de relations | Ne classe pas les clients |
| Régression logistique | C=0,1 et C=1 ; max_iter=2000 | Rapide, relation additive, régularisation | Relations non linéaires limitées |
| Forêt aléatoire | 100 arbres ; profondeur 8 / feuille min 10 et profondeur 16 / feuille min 5 | Interactions et non-linéarités | Extrapolation temporelle difficile |

4 scénarios × 5 configurations × 3 folds = **60 ajustements de CV**. Même seed 42. Un seul cœur par forêt pour limiter les ressources ; temps mesuré. Gradient boosting est laissé comme piste, pas ajouté sans justification après lecture du test.""",
)
code(
    30,
    """# 5.2 Expérience réelle enregistrée ; le code complet est dans train.py.
# Reproduction depuis zéro (terminal à la racine, si reports/final_test.json absent) :
# python -m bank_marketing.modeling.train
# python scripts/build_reports.py
# python scripts/evaluate_candidate.py
# Le script refuse d'écraser un test déjà évalué. Toute nouvelle passe exige
# des dossiers distincts et une entrée explicite au journal.
folds = pd.read_csv(REPORTS / 'cv_folds.csv')
assert len(folds) == 60
assert (folds.train_end < folds.validation_start).all()
display(folds[['scenario','model','fold','n_train','n','average_precision','roc_auc']])
print('Code reproductible :', inspect.getfile(training_module))
print('Run MLflow :', read_report('mlflow_run.json')['run_id'])
""",
)
md(
    31,
    """### 5.3 Métriques retenues & justification

**Average precision (AP)** sélectionne la qualité du classement sur une classe rare. Sa référence est la prévalence du bloc, qui change dans le temps : ne pas comparer une AP brute entre périodes sans cette référence. La ROC-AUC complète la lecture, mais peut sembler favorable malgré une précision insuffisante sur les positifs.

**Précision** = TP/(TP+FP) : parmi les prioritaires, combien souscrivent ? **Rappel** = TP/(TP+FN) : combien de souscripteurs sont repérés ? **F1** combine ces deux aspects. Le seuil maximise le F1 de validation parmi 0,05 à 0,80 par pas de 0,01, avec préférence au seuil supérieur en cas d'égalité. Ce choix ne prétend pas maximiser un profit inconnu.

**Precision@20 % et lift** donnent une lecture à capacité d'appels fixe, distincte du seuil F1. **Brier** et courbe de calibration confrontent probabilités et fréquences. Un seuil de 0,05 ne signifie pas une confiance de 95 % : il signifie simplement que la règle commence à classer positif à 5 % de probabilité estimée.

La CV est croissante dans l'ordre des observations avec un gap de 100 lignes. Faute de dates complètes, les fenêtres n'ont pas nécessairement la même durée. Un benchmark aléatoire stratifié sur le train seulement sert de sensibilité ; il n'est pas la preuve principale.""",
)
code(
    32,
    """# 5.4 Comparaison des modèles avec dispersion entre folds.
display(cv_results[['scenario','model','average_precision','average_precision_std',
                    'roc_auc','f1','brier','fit_seconds']].round(4))
figure('cv_scenarios.png')
display(pd.Series(read_report('random_cv_sensitivity.json')))
""",
)
md(
    33,
    """### 5.5 Optimisation des hyperparamètres

Recherche volontairement bornée : deux forces de régularisation logistique et deux couples profondeur/feuille pour la forêt. Les métriques sont évaluées sur les mêmes folds. Les résultats d'une recherche plus large ne sont pas revendiqués.

Règle figée : exclure S1 ; prendre les candidats S2–S4 non-Dummy à moins de 0,02 AP du meilleur, puis préférer moins de variables, AP supérieure et entraînement plus court. Cette tolérance absolue favorise fortement la minimisation lorsque les scores sont faibles : le gagnant technique n'est donc pas automatiquement un gagnant métier.

Un sigmoid est ajusté sur le bloc de calibration, puis contrôlé sur validation. Il n'est conservé que si le Brier s'améliore **et** que la pente reste positive pour conserver le sens du classement. Ici il est rejeté malgré l'amélioration de Brier : l'inversion du classement entre périodes signale de l'instabilité, pas une calibration fiable.""",
)
code(
    34,
    """# Preuve des réglages et du choix figé avant le test.
display(pd.Series(selection, name='Choix').to_frame())
print('Aucun refit sur le test. Le modèle final reste ajusté sur le train initial.')
""",
)
md(
    35,
    """### 5.6 Évaluation finale sur le test set

Le test a été ouvert **une fois** après enregistrement de `selection.json`. Les métriques ci-dessous proviennent de cette passe. Les lectures ultérieures, graphiques, audits de sous-groupes et bootstrap relisent ces mêmes prédictions ; elles ne sélectionnent pas un autre modèle.

La source avait déjà fait l'objet d'un contrôle global de comptes avant le protocole, ce qui est déclaré. Les intervalles bootstrap sont indicatifs et supposent des observations indépendantes ; ils ne couvrent ni la dépendance entre contacts d'un même client ni l'incertitude de dérive temporelle.""",
)
code(
    36,
    """# Résultat final et baseline historique, sans filtre d'abstention.
keys = ['n','prevalence','accuracy','precision','recall','f1','roc_auc',
        'average_precision','brier','precision_at_20','lift_at_20','selection_rate']
display(pd.DataFrame({'Candidat': {k: final[k] for k in keys},
                      'Dummy': {k: final['baseline'][k] for k in keys}}))
print('IC bootstrap AP 95 % :', final['ap_bootstrap_95_ci'])
figure('confusion.png')
figure('curves.png')
figure('calibration.png')
""",
)
md(
    37,
    f"""### 5.7 Synthèse modélisation

Candidat retenu par la règle : **{s['scenario']} / {s['model']}**, huit variables, seuil **{s['threshold']:.2f}**, sans calibration conservée. Sur test, AP **{f['average_precision']:.3f}** contre une prévalence **{f['prevalence']:.3f}**, ROC-AUC **{f['roc_auc']:.3f}**, F1 **{f['f1']:.3f}**. Le lift top 20 % est **{f['lift_at_20']:.2f}×**.

Mais sur validation, AP **{s['validation']['average_precision']:.3f}**, sous la prévalence **{s['validation']['prevalence']:.3f}**, et ROC-AUC **{s['validation']['roc_auc']:.3f}** : la performance n'est pas stable. Le seuil positif couvre {f['selection_rate']:.1%} du test, très différent du budget top 20 %. Aucun score final favorable n'efface ce défaut de validation.
""",
)
md(
    39,
    """### 6.1 Tableau comparatif et arbitrages

Les chiffres de CV comparables sont ci-dessous. Les temps d'entraînement, le p95 et le coût CPU d'inférence sont mesurés par configuration sur le train seulement, après sélection, sans modifier le choix. Ces 20 ajustements supplémentaires servent uniquement au benchmark opérationnel. Aucun coût en euros n'est inventé. La dépendance fournisseur d'inférence est nulle : calcul local sklearn.

| Scénario | Explicabilité | Risque et biais | Verdict |
|---|---|---|---|
| S1 | Dépend du modèle ; duration dominera souvent | Fuite d'information connue | Écarté du service quels que soient les scores |
| S2 | LogReg élevée ; forêt moyenne | Variables démographiques directes et disponibilité à auditer | Comparaison diagnostique |
| S3 | Même famille et même recette | Retrait des variables discutables ; proxys possibles | Comparaison minimisée |
| S4 | 8 variables, inspection simple mais corrélations macro | Écarts entre groupes et dérive toujours présents | Candidat pédagogique ; pas de promotion |

### 6.2 Recommandation finale au client
Ne pas utiliser ce candidat pour piloter une campagne réelle. Il illustre une capacité de classement historique, mais ne tient pas ses promesses sur validation et ne couvre pas la période finale avec les garde-fous retenus. Priorité : nouvelles données représentatives, contrôle de l'éligibilité au contact, validation temporelle glissante et revue d'équité avant une nouvelle décision.

### 6.3 Synthèse arbitrages
La minimisation réduit le nombre d'entrées, pas automatiquement les biais ni la dérive. La décision professionnelle est ici une non-promotion documentée, tout en livrant un service démontrable et une chaîne d'évaluation reproductible.""",
)
n.cells.insert(
    40,
    nbf.v4.new_code_cell(
        """display(pd.read_csv(REPORTS / 'scenario_arbitration.csv')[['scenario','model','average_precision','roc_auc','cpu_seconds_per_1000','p95_ms','explainability','provider_dependency','verdict']].round(4))
display(pd.read_csv(REPORTS / 'scenario_deltas.csv').round(4))
display(pd.read_csv(REPORTS / 'fairness_test.csv'))
figure('fairness_age.png')
print('Décision de promotion :', production)
"""
    ),
)


# Subsequent original indices shift by one.
def md2(i, text):
    md(i + 1, text)


def code2(i, text):
    code(i + 1, text)


code2(
    41,
    """# 7.1 Importance par permutation sur validation, pas sur le test.
display(pd.read_csv(REPORTS / 'permutation_importance.csv'))
figure('importance.png')
print('Une importance négative indique que la permutation améliore le score sur ce bloc.')
print('Les variables corrélées peuvent se substituer : ne pas lire cette importance comme un effet causal.')
""",
)
md2(
    42,
    """### 7.2 Analyse des erreurs et stratégies de fallback

Sur le test hors filtre, les faux positifs représentent des appels prioritaires sans souscription ; les faux négatifs représentent des souscripteurs historiques non identifiés. Les groupes diffèrent fortement : la suppression de l'âge n'empêche pas la sélection de profils corrélés à l'âge.

**Seuil de rejet** : catégorie valide mais non vue, valeur numérique hors min/max d'entraînement, ou probabilité à ±0,03 du seuil de décision. Les deux premiers cas ne publient pas de probabilité extrapolée. Le dernier cas conserve le score mais retire la décision.

**Abstention contrôlée** : HTTP 200, `abstain=true`, `prediction=null`, motif explicite et `action=human_review`. Les entrées invalides restent des erreurs HTTP 422, distinctes de l'incertitude du modèle.

**Reprise humaine** : responsable de campagne, objectif proposé d'un jour ouvré, vérification du profil et des droits de contact avant toute action. Le prototype n'a pas de connexion à une file de tickets d'entreprise ; l'action est exposée pour intégration. Le retrait des données hors domaine est prudent mais trop restrictif sur le test : nous ne modifions pas les seuils après lecture pour masquer cette limite.""",
)
code2(
    43,
    """# 7.2 Couverture réelle de la politique d'abstention.
display(pd.Series(read_report('fallback_test.json')))
display(pd.read_csv(REPORTS / 'fairness_test.csv').query("attribute == 'age_band'")
        [['group','n','selection_rate','fpr','fnr','small_sample']])
print('Couverture nulle : aucune performance conditionnelle de service ne peut être annoncée.')
""",
)
md2(
    44,
    f"""### 7.3 Message au client (langage métier)

« Nous avons construit et testé un outil qui estime la propension historique à souscrire. Parmi les 20 % de profils les mieux classés du dernier bloc, environ {f['precision_at_20']:.1%} ont souscrit, contre {f['prevalence']:.1%} dans l'ensemble du bloc. Ce résultat est descriptif, pas la preuve d'un gain causal lié à un appel.

Nous avons écarté la durée d'appel, car elle n'est connue qu'après la décision. Nous avons aussi testé une version réduite à huit informations. Toutefois, les périodes diffèrent fortement et les écarts d'erreurs entre groupes restent importants.

Nous recommandons de conserver ce service en démonstration. Une campagne réelle exige un nouvel échantillon récent, une validation plus stable, une revue de conformité et une vérification des permissions de contact. »

### 7.4 Synthèse interprétation
Trois messages : le piège de duration ; la différence entre score et utilité stable ; la non-promotion justifiée malgré une API fonctionnelle.
""",
)
md2(
    45,
    """---
## 8. Industrialisation

**Compétences : C6, C7.** Le code du service est dans `src/bank_marketing/service`, l'interface dans `ui`, les tests dans `tests` et les workflows dans `.github/workflows`. Ce cahier référence les preuves et décrit l'architecture ; il ne contient pas l'implémentation API.

Dépôt configuré : https://github.com/Nandodev-id/atlas-bank-marketing-ai — consulter l’onglet Actions du dépôt pour les résultats CI distants. Aucun déploiement réel n’est revendiqué.
""",
)
md2(
    46,
    """### 8.1 Persistance du modèle

`artifacts/model.joblib` conserve preprocessing, forêt, éventuel calibrateur, seuil, variables, référence et version. `model.sha256` vérifie l'intégrité ; `metadata.json` trace données/code/environnement. MLflow local archive un run réel. Les artefacts sont exclus de Git ; le ZIP de rendu et la reproduction les fournissent.

### 8.2 API de service

| Route | Méthode | Rôle | Contrôle |
|---|---|---|---|
| /health | GET | Modèle chargé | Public, statut minimal |
| /model | GET | Contrat et variables attendues | Bearer si configuré |
| /predict | POST | Probabilité ou abstention | Pydantic strict, colonnes exactes, contrôle OOD |
| /feedback | POST | Résultat observé lié à un identifiant | Validation, conflit refusé |
| /monitoring | GET | Labels, abstention, drift et demande de réentraînement | Agrégats, minimum de labels |
| /metrics | GET | Compteurs et histogrammes Prometheus | Bearer si configuré |
| /train | POST | Entraîner un candidat sur snapshot approuvé | Auth obligatoire, nouveau hash, un job par processus |
| /jobs/{id} | GET | État du candidat | Auth |

Le mode production refuse de démarrer sans clé. Le mode démo est lié à localhost. L'API ne valide jamais à elle seule le droit d'appeler.

### 8.3 Interface utilisateur

`streamlit run ui/app.py` ouvre le formulaire, les résultats et le suivi. Le formulaire interroge l'API, il ne charge pas l'artefact. Une API indisponible produit un message explicite. La preuve de validation est incluse dans `reports/verification.json` lorsqu'elle est disponible.

### 8.4 Schéma d'architecture

```mermaid
flowchart LR
 D[CSV approuvé] --> T[Pipeline CV / entraînement]
 T --> M[MLflow / artefact versionné]
 M --> G[Tests / gates / approbation humaine]
 G --> A[FastAPI]
 U[Streamlit] --> A
 A --> L[Audit SQLite / feedback]
 L --> S[Monitoring / demande de réentraînement]
 S --> T
```

Hypothèse d'hébergement : VM 2 vCPU/2 Go, sur site bancaire ou environnement validé SI/DPO. Pas de GPU nécessaire démontré. La latence ci-dessous est locale et séquentielle, sans garantie de charge.

### 8.5 Conteneurisation & CI/CD

Dockerfile non-root, secret requis, ressources limitées dans compose. CI : compilation et pytest. Pipeline candidat : snapshot HTTPS approuvé + hash, entraînement et tests, rapport de promotion, archivage. Déploiement conditionné par gates, environnement GitHub production et hôte configuré ; SSH vérifié, santé puis rollback vers l'image précédente si besoin.

Le socket Docker est inaccessible dans cette session : aucun build ni lancement de conteneur n'est revendiqué. Aucun serveur réel ni secret de déploiement n'a été configuré. Le candidat actuel échoue aux gates de production, donc ne doit pas être déployé. Le diagramme et les scripts sont livrés ; les captures d'un CI vert distant ou d'un Docker lancé ne sont pas fabriquées.

### 8.6 Synthèse industrialisation
Le service et ses contrats sont testés localement. La chaîne de livraison est définie et automatisée dans le dépôt, mais l'exécution sur hôte réel reste conditionnée à l'infrastructure et à une décision de promotion favorable. Un test logiciel réussi ne certifie pas l'utilité métier du modèle.
""",
)
# Evidence cell after original section 8 content: now index 48.
n.cells.insert(
    48,
    nbf.v4.new_code_cell(
        """display(pd.Series(read_report('api_smoke.json')))
display(pd.Series(read_report('api_example_response.json')))
print('Modèle p95 local (ms) :', final['model_latency_p95_ms'])
print('OpenAPI exporté : reports/openapi.json')
"""
    ),
)
# Original indices 47+ now shifted by two.
md(
    49,
    """---
## 9. Suivi en production & amélioration continue

**Compétences : C8, C9.** Le code de monitoring et la boucle de retour sont exécutables. Les données actuellement disponibles restent historiques ; les scénarios de surveillance ne sont pas présentés comme des mois d'exploitation réelle.""",
)
md(
    50,
    """### 9.1 Métriques à surveiller

| Type | Indicateur | Seuil proposé | Source et action |
|---|---|---|---|
| Technique | p95, erreurs 5xx, disponibilité | 500 ms, 1 %, objectif 99,5 % | Prometheus, alerte exploitation |
| Données | PSI par variable | > 0,2 après 100 requêtes | Référence entraînement, investigation |
| Modèle | AP avec résultats retardés | baisse > 0,05, au moins 200 labels et deux classes | /monitoring, demande candidat |
| Calibration | Brier, fréquence observée vs score | Revue mensuelle | Feedback ; examiner aussi la prévalence |
| Métier | Souscriptions à budget constant | Objectif à valider avec métier | Campagne contrôlée, pas simple métrique offline |
| Équité | Sélection/FPR/FNR par groupe | Revue avec effectifs | Analyse mensuelle et validation DPO |

Les seuils sont des hypothèses de projet, pas des standards universels. L'état actuel ne satisfait pas les conditions de promotion.

### 9.2 Boucle de rétroaction

Chaque prédiction reçoit un UUID. Un résultat `yes/no` est relié par /feedback, avec version du modèle. Les retours contradictoires sont refusés. Les résultats des non-contactés peuvent manquer : ne pas les fabriquer comme négatifs. La collecte terrain doit documenter ce biais et prévoir un échantillon de contrôle.

### 9.3 Plan de réentraînement

Un indicateur dégradé demande un candidat, pas son déploiement. /train exige un snapshot approuvé différent du jeu d'examen. La CI hebdomadaire est activée seulement si une source approuvée est configurée ; elle effectue entraînement, évaluation et gates. Champion/challenger doivent être confrontés sur une fenêtre récente commune, indépendante de leur entraînement, avant revue humaine. Le présent pipeline entraîne et filtre un candidat ; le script `scripts/compare_challenger.py` réalise cette comparaison sans entraînement sur une fenêtre approuvée et contrôle les chevauchements exacts. Aucune comparaison prospective réelle n'a eu lieu faute de nouvelles données.

### 9.4 Robustesse en exploitation

- **OOD** : plages et catégories apprises sur train ; abstention et journalisation du motif, sans appel automatique.
- **Dérive de l'abstention** : suivre couverture et fréquence de révision humaine ; une couverture nulle impose une suspension et une nouvelle analyse, pas un assouplissement silencieux.
- **Calibration** : Brier et courbe avec résultats observés ; recalibration sur données dédiées puis validation indépendante. Ici le sigmoid à pente négative n'est pas conservé.
- **Rollback** : health check après mise à jour ; restauration de l'image précédente si échec. Test en préproduction requis.

### 9.5 Synthèse amélioration continue
La surveillance relie chaque score à une version et à un retour observé. Elle peut déclencher une demande d'entraînement, mais la promotion reste séparée, vérifiable et réversible. Le périmètre et les indicateurs doivent être revus chaque trimestre avec métier, SI et DPO.
""",
)
md(
    51,
    """---
## Annexes

### A. Glossaire métier & technique

- Dépôt à terme : produit d'épargne auquel se rapporte la cible du sujet.
- Feature : variable d'entrée ; cible : résultat à prédire.
- Leakage : information indisponible au moment réel de décision.
- CV : validation croisée ; OOT : évaluation sur une période ultérieure.
- AP : moyenne de précisions pondérées par les incréments de rappel ; ne pas la confondre avec l'accuracy.
- Calibration : accord entre probabilité et fréquence observée.
- OOD : donnée hors du domaine de référence.
- Champion/challenger : modèle en service et candidat évalué avant remplacement.
- FPR : faux positifs / négatifs réels ; FNR : faux négatifs / positifs réels.

### B. Sources & bibliographie

- Sujet d'examen fourni, pages 1–6 ; dictionnaire p.5–6.
- [Canevas Simplon officiel](https://github.com/Formation-SIMPLON-IA/ia-dev-id-ressources/blob/main/cas_usage_certif/canvas-cas-usage-v2.ipynb).
- [UCI Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing), DOI 10.24432/C5K306 ; variante additionnelle ordonnée, licence CC BY 4.0.
- [scikit-learn TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html), principe de fenêtres croissantes et réserve sur l'espacement des observations.
- [CNIL : démarchage](https://cnil.fr/fr/demarchage-commercial) ; [RGPD principes](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre2) ; [droits](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre3) ; [analyse d'impact](https://cnil.fr/fr/realiser-une-analyse-dimpact-si-necessaire). Vérifiés le 18/10/2026.

**Analyse juridique synthétique** : distinguer données personnelles, catégories particulières de l'article 9 et variables commercialement discutables. Examiner séparément base du développement et base de l'usage. En France, depuis août 2026, consentement préalable au démarchage téléphonique ou exception applicable ; le modèle ne fournit pas cette preuve. La conservation de 30 jours proposée dans le prototype doit être validée. Voir `docs/ETHIQUE_ET_CONFORMITE.md` pour le raisonnement complet.

### C. Décisions techniques détaillées

`docs/ARCHITECTURE_ET_EXPLOITATION.md` documente contraintes, ressources, sécurité, reprise humaine et limites. `config/protocol.json` conserve les décisions initiales. `reports/production_decision.json` applique la revue de promotion. L'absence de promotion est une conclusion du projet.

### D. Journal de bord

Voir [journal-de-bord.ipynb](journal-de-bord.ipynb) pour les étapes datées et les décisions.
""",
)
journal = nbf.v4.new_notebook(
    cells=[nbf.v4.new_markdown_cell(
        """# Journal de bord — Atlas

| Étape du 18/10/2026 | Travail / résultat / justification |
|---|---|
| Audit initial | Lecture des six pages, source vérifiée, projet au stade fondation ; comptes globaux déjà vus |
| Référence | Canevas officiel récupéré, ancien squelette sauvegardé |
| Cadrage | Décision avant appel, exclusions, métriques et critères explicités |
| Environnement | Venv local adossé à Anaconda existant ; versions archivées ; aucune modification de l'environnement global |
| Protocole | 60/10/10/20, CV croissante, scénarios et sélection fixés avant entraînement |
| Expériences | 60 fits CV, choix S4 forêt profondeur 8, calibration rejetée, seuil 0,05 |
| Test n°1 | Une ouverture après gel ; prédictions archivées, aucune nouvelle sélection fondée sur test |
| Audit final | Sous-groupes, drift et couverture : 0 % de couverture ; décision non-promotion |
| Gates complémentaires | Seuil couverture 80 % et écarts 20 points ajoutés lors de la revue, explicitement postérieurs, sans réajuster le modèle |
| Service | API, feedback, entraînement candidat séparé, monitoring et tests synthétiques |
| Livraison | Notebook exécuté, rapports, CI/CD et conteneurisation fournis ; Docker et hôte réel non exécutés |

## 19 octobre 2026

Réorganisation du livrable : README technique condensé, canevas officiel séparé, point d’entrée API standard et notes de préparation déplacées hors dépôt. Comparaison des structures des dépôts de 3ti3nne et nawellepolin ; aucun code ou résultat de ces projets repris.
"""
    )]
)
nbf.write(journal, ROOT / "notebooks/journal-de-bord.ipynb")

for cell in n.cells:
    if cell.cell_type == "markdown" and "Cette section est la base de ton pitch" in cell.source:
        cell.source = "## 7. Interprétation et communication\n\nAnalyse des facteurs prédictifs, des erreurs et des limites ; synthèse des résultats en langage métier."

# Add real monitoring diagnostic without any additional selection.
n.cells.insert(
    51,
    nbf.v4.new_code_cell(
        """display(pd.read_csv(REPORTS / 'drift_test.csv'))
# Exercice synthétique de déclenchement, distinct de résultats terrain.
display(retraining_decision([0,1]*150, [0.9,0.1]*150, reference_ap=0.8))
print('Aucun déploiement automatique :', production['recommendation'])
"""
    ),
)
n.metadata.kernelspec = {"display_name": "Atlas Python", "language": "python", "name": "atlas"}
nbf.validate(n)
nbf.write(n, ROOT / "notebooks/certification.ipynb")
# Exploration notebook points at the same frozen training split and is independently runnable.
e = nbf.v4.new_notebook(
    cells=[
        nbf.v4.new_markdown_cell(
            "# Exploration Atlas — bloc d’entraînement\nLes décisions complètes figurent dans certification.ipynb."
        ),
        n.cells[4],
        n.cells[6],
        n.cells[10],
        *n.cells[13:19],
    ]
)
e.metadata.kernelspec = n.metadata.kernelspec
nbf.write(e, ROOT / "notebooks/exploration.ipynb")
print("Certification notebook:", len(n.cells), "cells; all official sections filled.")
