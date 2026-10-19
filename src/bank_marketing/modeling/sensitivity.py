"""Post-evaluation scenario comparison on development data; never fit on final test."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

from .core import make_pipeline, scenarios


def load_development(path, splits):
    """Read only the pre-test CSV prefix and select frozen development indices."""
    development = [int(i) for key in ('train', 'calibration', 'validation') for i in splits[key]]
    test = set(splits['test'])
    if not development or not test:
        raise ValueError('Development and held-out test must both be defined')
    if len(set(development)) != len(development) or set(development) & test:
        raise ValueError('Frozen splits overlap')
    if min(development) < 0 or max(development) >= min(test):
        raise ValueError('Development must precede the final test')
    # No final-test feature values or labels are parsed by this experiment.
    frame = pd.read_csv(path, sep=';', nrows=max(development) + 1).loc[sorted(development)]
    features = [c for c in frame if c != 'y']
    clean = frame.drop_duplicates(subset=features, keep='first').copy()
    return clean, len(frame) - len(clean)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('data/raw/bank-additional-full.csv'))
    parser.add_argument('--splits', type=Path, default=Path('artifacts/split_indices.json'))
    parser.add_argument('--output', type=Path, default=Path('reports/sensitivity'))
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit('Use a new empty output directory to preserve prior evidence')
    splits = json.loads(args.splits.read_text())
    frame, duplicates = load_development(args.data, splits)
    y = frame.y.eq('yes').astype(int)
    if y.value_counts().min() < 5:
        raise ValueError('Five-fold stratification needs at least five rows per class')
    folds = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=42).split(frame, y))
    models = {
        'logreg_C1': LogisticRegression(C=1, max_iter=2000, random_state=42),
        'rf_depth8': RandomForestClassifier(
            n_estimators=100, max_depth=8, min_samples_leaf=10, n_jobs=1, random_state=42
        ),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    assignments = pd.Series(index=frame.index, dtype='int64', name='fold')
    for fold, (_, va) in enumerate(folds, 1):
        assignments.loc[frame.index[va]] = fold
    assignments.rename_axis('source_row').astype(int).to_csv(args.output / 'fold_assignments.csv')
    results = []
    for scenario, features in scenarios(frame.columns).items():
        for model_name, model in models.items():
            for fold, (tr, va) in enumerate(folds, 1):
                pipeline = make_pipeline(features, model)
                pipeline.fit(frame.iloc[tr][features], y.iloc[tr])
                probability = pipeline.predict_proba(frame.iloc[va][features])[:, 1]
                results.append(dict(
                    scenario=scenario, model=model_name, fold=fold,
                    n_train=len(tr), n_validation=len(va), n_features=len(features),
                    prevalence=float(y.iloc[va].mean()),
                    roc_auc=float(roc_auc_score(y.iloc[va], probability)),
                    average_precision=float(average_precision_score(y.iloc[va], probability)),
                ))
            print(f'{scenario} {model_name}: five folds complete', flush=True)
    scores = pd.DataFrame(results)
    scores.to_csv(args.output / 'fold_scores.csv', index=False)
    summary = scores.groupby(['scenario', 'model'], sort=False).agg(
        n_features=('n_features', 'first'),
        roc_auc_mean=('roc_auc', 'mean'), roc_auc_std=('roc_auc', 'std'),
        average_precision_mean=('average_precision', 'mean'),
        average_precision_std=('average_precision', 'std'),
        prevalence=('prevalence', 'mean'),
    ).reset_index()
    summary.to_csv(args.output / 'comparison.csv', index=False)
    ranges = []
    for block in ['train', 'calibration', 'validation']:
        part = frame.loc[frame.index.intersection(splits[block])]
        for feature in ['emp.var.rate', 'cons.price.idx', 'cons.conf.idx', 'euribor3m', 'nr.employed']:
            ranges.append(dict(block=block, feature=feature, minimum=float(part[feature].min()),
                               maximum=float(part[feature].max()), unique_values=int(part[feature].nunique())))
    pd.DataFrame(ranges).to_csv(args.output / 'development_macro_ranges.csv', index=False)
    metadata = dict(
        created_at=datetime.now(timezone.utc).isoformat(),
        purpose='Post-evaluation exploratory sensitivity; no model reselection or promotion',
        population='Frozen train + calibration + validation; final test excluded',
        n_development=len(frame), removed_duplicate_profiles=duplicates,
        development_max_source_row=int(frame.index.max()), first_test_source_row=min(splits['test']),
        final_test_rows_read=0, final_test_labels_used=False,
        splits_sha256=hashlib.sha256(args.splits.read_bytes()).hexdigest(),
        cv='StratifiedKFold', n_splits=5, shuffle=True, random_state=42,
        fixed_models=['logreg_C1', 'rf_depth8'], fits=len(results),
        preprocessing='Fitted independently inside each training fold; shared validation folds for all scenarios',
        duplicates='Identical full predictor profiles removed before splitting, first row retained; no client identifier available',
        dispersion='Sample standard deviation across five folds, not a confidence interval',
        limitations=['Not an independent confirmation: development data already used in the original study',
                     'Mixes periods and cannot establish future temporal generalization',
                     'Different population from original CV (first 60% only): score differences are not solely a split-method effect',
                     'S1 includes duration and is a leakage diagnostic, never deployable before calling',
                     'No threshold tuning, final-test rescoring or serving-artifact replacement'],
    )
    (args.output / 'protocol.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n')
    print(summary.round(4).to_string(index=False))


if __name__ == '__main__':
    main()
