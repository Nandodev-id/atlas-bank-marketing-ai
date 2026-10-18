> Historique de la première étape, conservé pour traçabilité. Pour l’état final, lire le README, le notebook de certification et `COUVERTURE_EXAMEN.md`.

# Session 1 — Foundation checklist

- [x] Parse the learner-supplied CSV and confirm row count, columns, target distribution, duplicate rows and sentinel frequency.
- [x] Preserve raw bytes and record SHA-256.
- [x] Define package skeleton and initial data contract.
- [x] Add automated tests for source-data inspection.
- [x] Add certification notebook structure derived from the nine-part Simplon canvas.
- [x] Add GitHub Actions CI definition.
- [ ] Create a **private** GitHub repository under the learner's preferred account.
- [ ] Clone/push this starter from the learner's Mac; verify remote URL and Git identity.
- [ ] Install Python dependencies on the learner's Mac and run checks.
- [ ] Record local Python version and the first successful GitHub Actions run.

## What Session 1 deliberately does not include

No statistical model training, parameter tuning, API endpoint, deployment, or claims of validated predictive performance. Later phases require separate reviews.

## GitHub: private repository creation from the Mac

For an existing downloaded project (after unzipping and opening the directory):

```bash
# Check you're authenticated to the correct account first:
gh auth status
# Initialize git and publish as a private repo; requires GitHub CLI:
git init -b main
git add .
git commit -m "chore: bootstrap atlas bank marketing project"
gh repo create atlas-bank-marketing-ai --private --source=. --remote=origin --push
```

**Important:** confirm the active GitHub account and make sure this is the desired personal/work profile. The connected account observed in chat was `Nandodev-id`, which may not be the preferred owner. Do **not** publish data/raw/bank-additional-full.csv (it is ignored by default).

If `gh` is not installed, create a **private, empty repository** at https://github.com/new (do not initialize README/LICENSE/gitignore), then run `git remote add origin git@github.com:YOUR_ACCOUNT/atlas-bank-marketing-ai.git` and `git push -u origin main` after authentication is set up.

## Optional: obtain the exact official Simplon canvas

After connecting your Mac to the internet, run:

```bash
python scripts/fetch_simplon_canvas.py
```

This stores the canonical canvas as `notebooks/simplon_reference_canvas.ipynb`, leaving our own `notebooks/certification.ipynb` unchanged.
