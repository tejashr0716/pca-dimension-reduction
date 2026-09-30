# Verification of this rebuild

- Local pytest: **73 passed**, zero failures/errors/skips.
- Local browser checks: **13 passed** with no unhandled JavaScript exceptions.
- Browser: Chromium, desktop 1280px and mobile 390px; light and dark modes.
- Ruff lint/format checks and installed dependency checks passed.
- The real browser sample button called the analysis API and downloaded a CSV with 1,921 rows and 12 component columns.
- PCA retained **99.718971735986%** of standardized variance.
- An independent manually scaled covariance-eigenvalue calculation reproduced the metric within 1.42e-14 percentage points.

Evidence: `benchmark.json`, `verification.json`, and `browser-verification.json` in this folder.

The dataset is synthetic and deliberately correlated. 2,000 input rows become 1,921 complete rows after cleaning. These numbers are not a classification accuracy score, a universal CSV guarantee or a deployment performance claim.

The browser checks include a simulated expired-download HTTP response and an intentionally blocked chart asset to test recovery. Actual cache expiration is independently covered by pytest.

## Reproduce locally

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/benchmark.py
ruff check .
ruff format --check .
```

For a manual browser repeat, use the demo and live acceptance steps in `INTERVIEW_GUIDE.md` and `DEPLOYMENT.md`. The GitHub Actions matrix is configured, not remotely verified in this session. The local Python/package versions are recorded in `benchmark.json`.

This local QA record was captured before source publication. The initial GitHub
write-access problem was subsequently resolved. The rebuild is now published
in the repository, with the original version retained on a backup branch.
See `publication.json` and the project links in `README.md` for deployment status.
