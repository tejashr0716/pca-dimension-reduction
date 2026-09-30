# Replace the project safely

## Source publication and live deployment

The rebuilt source is published on `main`. The running Flask app is
[PCA Lab](https://pca-dimension-reduction.onrender.com), hosted by Render on the free plan in
Singapore. It deploys automatically from this repository’s `main` branch.
GitHub source hosting and the running Python service are separate.

The public HTTPS acceptance checks passed: home page and assets, the original
benchmark CSV, real analysis, reduced CSV download and representative input
errors. See `docs/live-verification.json`. GitHub Actions also passed on Python
3.11, 3.12 and 3.13.

The original version is preserved at branch
`backup/pre-pca-rebuild-2026-09-30`, commit
`63eeaace8a95c894e8cc524526c61ee1bd2f11bf`.
No credential is included in the repository. Do not paste tokens into chat or
commit them to Git. `docs/verification.json` records the earlier local QA run;
`docs/publication.json` records publication/deployment status separately.

## Local preview on Windows

Install Python 3.11–3.13, extract the ZIP, and open a terminal in the extracted
`pca-dimension-reduction` folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python app.py
```

Open `http://127.0.0.1:5000`. In another terminal:

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python scripts\benchmark.py
```

You do not need to activate the environment or change PowerShell's execution
policy when calling its Python executable directly. Gunicorn is for Linux
deployment, not Windows local development.

## Local preview on Linux/macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python app.py
```

For reproducible verification and a lightweight production-server smoke test:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q
OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/benchmark.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/gunicorn -c gunicorn.conf.py app:app
```

Gunicorn defaults to port 8000; hosting providers can supply `PORT`.

## Make future replacements safely

The initial rebuild is already published; these are maintenance instructions,
not remaining setup steps. Use a fresh clone to avoid overwriting unrelated
local work:

```bash
git clone https://github.com/tejashr0716/pca-dimension-reduction.git pca-replacement
cd pca-replacement
git switch -c rebuild/pca-interview-ready
```

Copy the contents of the ZIP's project folder into this clone, replacing the
same-named files. Include the hidden `.github` directory and `.gitignore`.
Never delete or replace the clone's `.git` directory. Do not copy `.venv`,
temporary results, cache directories or credentials.

Install dependencies, run tests, and run the benchmark as above. Then:

```bash
git status
git add .gitignore .github app.py pca_pipeline generate_sample_data.py requirements.txt requirements-dev.txt pyproject.toml gunicorn.conf.py Procfile render.yaml README.md START_HERE.md templates static tests scripts docs
git diff --cached --stat
git commit -m "Rebuild PCA demo with reproducible benchmark and validation tests"
git push -u origin rebuild/pca-interview-ready
```

The included sample file is unchanged from the original repository. Inspect
the staged diff before committing; do not use `git add .` without checking for
private files. Create a GitHub pull request into `main`; review CI and merge
only when you are ready to replace the current version. Keep the old commit
available for rollback. Do not rewrite old commit dates or history.

## Hosting

The current service is `pca-dimension-reduction` on Render’s free plan.
It uses Python 3.12.11, one Gunicorn worker and two threads. The running URL is
listed above and in the README. Automatic deployment follows `main`.

A free service can sleep after 15 idle minutes and take about a minute to
restart. This is a demo, not an always-on production service. See
[Render’s free-service documentation](https://render.com/docs/free).

### Existing deployment

Keep the current service and public URL if it already follows this repository.
Confirm the deployed branch, root directory and Python version. Use:

```text
Build: pip install -r requirements.txt
Start: gunicorn -c gunicorn.conf.py app:app
Python: 3.11, 3.12 or 3.13
OPENBLAS_NUM_THREADS=1
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
```

Merge the reviewed rebuild, redeploy through the host, and run the live
acceptance checklist below. Do not delete the old service first.

### Recreate the Render service if needed

`render.yaml` is a starting configuration for a Python web service. In Render,
connect the repository, choose the reviewed branch and use the build/start
commands above (or a Blueprint from the YAML). The configuration requests a
free plan; provider availability, limits and pricing can change. Check them
in your account. Do not provision a paid plan without intending to do so.

A service has now been created and verified at the URL above. The YAML remains
a reproducible starting point; it does not automatically migrate another
existing service or its URL.

### Critical single-worker limitation

Leave `workers = 1` in `gunicorn.conf.py`. The in-memory result store is shared
by threads, not by worker processes or replicas. Multiple workers/replicas
require a different shared result store; increasing worker count alone can
break downloads. Restarts and free-service sleep cycles clear cached results.

## Live acceptance checklist

- The home page, CSS, local Chart.js and application script load.
- The sample button performs a real upload and returns the 99.7%-rounded result.
- Audit shows 2,000 input rows, 1,921 complete rows and 79 dropped rows.
- Both chart views and the variance table agree.
- Download produces 1,921 rows and 12 PC columns.
- Malformed CSV and an out-of-range component count return visible errors.
- A request above 50 MB returns 413 (a proxy may impose a smaller limit).
- Test keyboard controls and a narrow/mobile viewport.
- Check host logs for unexpected 500s; do not log bearer tokens or uploaded data.
- Update your portfolio link only after the live demo passes.

## Rollback

Use the hosting provider's prior-deployment rollback or revert the rebuild
merge commit through a new reviewed commit. Do not force-push away history.
Cached downloads will be cleared by a restart; users can rerun analyses.