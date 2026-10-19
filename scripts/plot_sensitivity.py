"""Plot frozen complementary CV scores without refitting or accessing test data."""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
table = pd.read_csv(root / 'reports/sensitivity/comparison.csv')
fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))
labels = ['S1*', 'S2', 'S3', 'S4']
for ax, metric, title in zip(axes, ['roc_auc', 'average_precision'], ['ROC-AUC', 'Average precision']):
    for offset, model, label, color in [(-0.07, 'logreg_C1', 'Régression logistique', '#2266aa'),
                                        (0.07, 'rf_depth8', 'Forêt', '#c55722')]:
        rows = table[table.model == model].set_index('scenario').loc[['S1','S2','S3','S4']]
        ax.errorbar(np.arange(4) + offset, rows[metric + '_mean'], yerr=rows[metric + '_std'],
                    fmt='o-', capsize=4, color=color, label=label)
    baseline = 0.5 if metric == 'roc_auc' else float(table.prevalence.iloc[0])
    ax.axhline(baseline, linestyle='--', color='gray', linewidth=1, label='Référence sans discrimination')
    ax.set_xticks(range(4), labels)
    ax.set_ylim(0.45 if metric == 'roc_auc' else 0, 1 if metric == 'roc_auc' else 0.60)
    ax.set_title(title)
    ax.grid(alpha=0.18)
axes[0].legend(fontsize=8, loc='lower right')
fig.suptitle('CV stratifiée complémentaire — développement uniquement', fontsize=13)
fig.text(0.5, 0.035, '5 folds communs · moyenne ± écart-type · test final exclu\n*S1 inclut duration : diagnostic de fuite, non exploitable avant appel', ha='center', fontsize=9)
fig.tight_layout(rect=(0, 0.10, 1, 0.94))
fig.savefig(root / 'reports/figures/stratified_comparison.png', dpi=150)
plt.close(fig)
