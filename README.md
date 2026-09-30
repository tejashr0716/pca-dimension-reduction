# PCA Lab — CSV Dimensionality Reduction

An explainable Flask application for uploading a numeric CSV, cleaning and
standardizing its features, applying PCA, inspecting retained variance, and
downloading the component scores.

**This is a portfolio-scale demo, not a confidential-data service.**

## Project links

- [Source repository](https://github.com/tejashr0716/pca-dimension-reduction)
- [Interview guide](docs/INTERVIEW_GUIDE.md)
- [Benchmark evidence](docs/benchmark.json)
- [Automated checks](https://github.com/tejashr0716/pca-dimension-reduction/actions/workflows/tests.yml)
- [Live PCA Lab demo](https://pca-dimension-reduction.onrender.com)
- [Download the original 100-feature sample CSV](https://pca-dimension-reduction.onrender.com/sample_100d_data.csv)
- [Public-service verification](docs/live-verification.json)

The demo is hosted on Render’s free plan. After 15 minutes without traffic it
may sleep; the first request can take about a minute to wake it. Restarts/sleep
clear temporary analysis results, so rerun the analysis if a download expires.
See [Render’s free-service limits](https://render.com/docs/free).

## What is implemented

- Two REST endpoints: `POST /api/analyze` and `GET /api/download`.
- A responsive JavaScript frontend using async `fetch` and locally served Chart.js.
- Strict UTF-8 CSV structure checks, numeric dtype selection, explicit row
  deletion, constant-column removal, `StandardScaler`, and full-SVD `PCA`.
- Component and cumulative variance views, preprocessing audit, PC score
  preview, component weights, and reduced CSV download.
- Eleven documented primary failure classes, plus size/concurrency/numerical safeguards.
- An expiring, thread-safe result cache: 16 entries / 64 MiB / 15-minute nominal TTL.
- Automated API, numerical, cache and benchmark tests; a GitHub Actions workflow.
- A reproducible benchmark with an independent covariance-eigenvalue check.
- Interview and deployment walkthroughs.

The API computes all values from the uploaded file. No preset 99.7% result is
inserted into an analysis or chart.

## Quick start

Python 3.11–3.13:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python app.py
```

Open `http://127.0.0.1:5000` and click **Try the 100-feature sample**.
Windows commands and hosting instructions are in
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Reproduce the resume metric

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m pytest -q
OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/benchmark.py
```

The repository's original seed-42 sample has **2,000 rows and 100 numeric
features**. It deliberately contains 12 Gaussian latent factors plus noise,
and 80 missing cells. Complete-case cleaning removes **79 rows**, leaving
**1,921 rows**. Retaining **12 components** preserves about
**99.718971736% of standardized variance**, which rounds to **99.7%**.

Saved evidence: [docs/benchmark.json](docs/benchmark.json).
Your new run writes `artifacts/benchmark.json`.
The generator remains available with:

```bash
.venv/bin/python generate_sample_data.py --output artifacts/regenerated.csv
```

This synthetic dataset is intentionally favorable to PCA. The metric is not
classification accuracy, not a universal 12-component guarantee, and not
lossless or fixed-size file compression.

## API

```bash
curl -F "file=@sample_100d_data.csv" -F "components=12" \
  http://127.0.0.1:5000/api/analyze
curl -o pca_reduced_data.csv \
  "http://127.0.0.1:5000/api/download?analysis_id=REPLACE_WITH_RETURNED_ID"
```

Success JSON includes the result ID/download URL, full-precision variance
ratios, cumulative percentages, row and column audit, top component weights,
timing and a 10-row score preview. Errors use:

```json
{"error": {"code": "COMPONENTS_OUT_OF_RANGE", "message": "Use 1 to 100 components after cleaning and removing constant columns."}}
```

The maximum component count is `min(complete_rows - 1, variable_numeric_features)`.
The actual bound depends on the uploaded dataset.

## Limits and limitations

- **50,000,000 bytes** maximum whole HTTP request, including multipart overhead.
- At most **50,000 rows**, **500 columns**, and **2,000,000 source cells**.
- One active analysis per process; a concurrent analysis returns 429.
- In-memory results may be evicted early or cleared by a restart.
- Deploy with **one Gunicorn worker**; multiple workers/replicas need shared storage.
- No login, user ownership checks, distributed job queue or per-user rate limiting.
- Complete-case deletion can introduce bias; mixed text/numeric columns are skipped.
- Numeric identifiers/labels, outliers and domain-specific scaling need user judgment.
- This API fits a fresh transformation for each file. For predictive ML,
  fit preprocessing/PCA on training data only and transform the held-out data.

Do not upload personal or sensitive data to a public deployment.

## Source map

```text
app.py                       HTTP, limits, cache, responses
pca_pipeline/pipeline.py      Validation and numerical pipeline
pca_pipeline/store.py         Bounded result cache
generate_sample_data.py       Original synthetic data recipe
templates/index.html          Accessible workspace
static/app.js                 Browser state, fetch and chart wiring
static/chart-runtime.js       Provided formatting/tooltip/audit helpers
static/vendor/                Pinned Chart.js and MIT license
tests/                        API, pipeline, cache and benchmark regressions
scripts/benchmark.py          Independent metric verification
docs/INTERVIEW_GUIDE.md        Library choices, math, demo and practice questions
docs/DEPLOYMENT.md             Safe replacement, hosting and rollback
gunicorn.conf.py              Single-worker production server
render.yaml                   Optional hosting starting configuration
```

## Code quality

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest -q
```

The workflow configures checks for Python 3.11, 3.12 and 3.13. That configuration
does not itself mean remote CI or a live deployment has run.

## Interview preparation

Read [docs/INTERVIEW_GUIDE.md](docs/INTERVIEW_GUIDE.md), trace a request through
the source, reproduce the benchmark and perform the suggested experiments.
Keep resume dates and authorship claims tied to work you actually performed.

Built for Tejas HR's PCA portfolio project.