# PCA Pipeline: understand it before you showcase it

This is a rebuild of the existing project. Do not claim a skill, date, test
result or design decision as your own until you have worked through it and
can demonstrate it. Rebuild work does not establish that it existed in
November–December 2025; keep those dates only if they describe your actual work.

## 1. Your 45-second project explanation

Use this as practice, not a script to memorize without understanding:

> This is a Flask application that reduces numeric CSV features using PCA.
> It validates the upload and component count, selects numeric columns,
> removes rows with missing or infinite values, and removes constant columns.
> A scikit-learn Pipeline standardizes the data and applies full-SVD PCA.
> The JavaScript frontend uses fetch without a page reload, and Chart.js
> shows each component's contribution and cumulative retained variance.
> A second endpoint downloads the reduced scores. On the repository's
> seeded synthetic benchmark, 100 features become 12 components with about
> 99.7% of standardized variance retained. That is a measured benchmark
> result, not an accuracy score or a guarantee for arbitrary CSVs.

## 2. What exactly happens when you click Run PCA?

Read these files in this order:

1. `templates/index.html`: semantic controls and placeholders; no PCA calculations.
2. `static/app.js`: selected-file state, client checks, FormData, async fetch.
3. `app.py`: HTTP validation, concurrency guard, pipeline call, cache and JSON.
4. `pca_pipeline/pipeline.py`: the actual numerical and CSV processing.
5. `pca_pipeline/store.py`: bounded, expiring reduced-CSV storage.
6. `tests/test_api.py`: documented failure classes and successful round trips.
7. `scripts/benchmark.py`: independent reproduction of the resume number.

Flow:

```text
CSV + component count
  -> POST /api/analyze (multipart/form-data)
  -> strict CSV structure and UTF-8 checks
  -> pandas numeric dtype selection
  -> NumPy finite-row mask
  -> remove constant columns
  -> StandardScaler.fit_transform
  -> PCA(full SVD).fit_transform
  -> PC score CSV + explained variance + preprocessing audit
  -> bounded in-memory cache -> JSON response
  -> DOM updates and Chart.js
  -> GET /api/download?analysis_id=... -> CSV attachment
```

## 3. Why each library exists

| Library | Actual use | Why use it here? | Alternative / trade-off |
|---|---|---|---|
| Python | Backend and numerical orchestration | Fits the scientific Python ecosystem | Java/JS possible, but different ML tooling |
| Flask | Routing, multipart uploads, JSON, templates, downloads | Small two-endpoint synchronous service | FastAPI useful for typed API-first services; not needed just to claim another framework |
| pandas | CSV parsing, dtype selection, CSV export and preview | Maintains named columns and tabular operations | NumPy alone needs additional parsing/column handling |
| NumPy | Dense arrays, finite masks, cumulative sums, independent covariance check | Vectorized numerical operations | Python loops are more verbose and unsuitable for large numerical matrices |
| scikit-learn | StandardScaler, Pipeline and PCA | Established numerical implementations and consistent fit/transform interfaces | Manual SVD is useful for verification, not necessary as the application's implementation |
| JavaScript | File state, FormData, fetch and DOM rendering | Makes the frontend interactive without a framework | A framework adds dependencies with little value for one workspace |
| Chart.js | Component variance and cumulative-variance views | Responsive canvas plots with established chart primitives | SVG or another chart package; no need for 3D or unrelated plot types |
| pytest | Parameterized API and numerical regression tests | Makes validation and the benchmark repeatable | unittest is also valid |
| Gunicorn | WSGI production process | Avoids deploying Flask's development server | Platform-managed WSGI hosting is another option |

Chart.js is pinned and served locally with its MIT license. Chart formatting,
tooltip and validation helpers are a provided support module in
`static/chart-runtime.js`; application-specific chart wiring is in
`static/app.js`. Do not imply that you authored third-party or provided code.

## 4. PCA without buzzwords

- A row is an observation; a numeric column is an input feature.
- PCA is **unsupervised linear dimensionality reduction**, not a classifier.
- Principal components are orthogonal directions in feature space.
- Each output PC column contains the projection score for each retained row.
- PC1 explains the most variance; PC2 explains the most remaining variance
  subject to being orthogonal to PC1, and so on.
- PCA is **feature extraction**, not selecting 12 original features.
- Orthogonal component directions give uncorrelated scores on the fitted
  data. Uncorrelated does not generally mean statistically independent.
- Components' signs can flip: a direction and its negative describe the
  same axis. Variance and reconstruction are unchanged.
- No target labels, training accuracy, classifier or neural network is involved.

For an `n x p` standardized matrix `X`, SVD is:

```text
X = U S V^T
first k PC directions = first k rows of V^T
score matrix = X V_k = U_k S_k
explained variance for PC i = S_i^2 / (n - 1)
explained variance ratio = PC variance / total variance of standardized X
```

The application uses the library implementation. The benchmark independently
checks it with manually standardized data and covariance eigenvalues.

## 5. Why StandardScaler?

Without scaling, a feature measured in thousands may dominate one measured
in fractions merely because of its units. This project chooses:

```text
scaled value = (value - feature mean) / feature population standard deviation
```

`StandardScaler` uses `ddof=0`; PCA's eigenvalue/sample variance formula uses
`n-1`. The common denominator cancels in the explained-variance ratio.

Scaling is a **choice**, not always mandatory. If meaningful original feature
variances should retain their relative importance, covariance PCA without
unit-variance scaling may be preferable. Outliers can affect both the scaler
and PCA; this demo does not implement robust scaling or outlier removal.

## 6. Defend 100 -> 12 and 99.7% honestly

The original generator is preserved:

```text
seed = 42
Z: 2,000 rows x 12 normally distributed latent factors
W: 12 x 100 normally distributed feature loadings
noise: 2,000 x 100, Gaussian standard deviation 0.18
X = Z @ W + noise
80 randomly located cells replaced with NaN
```

Measured on the included file:

| Quantity | Value |
|---|---:|
| Generated/input rows | 2,000 |
| Numeric features | 100 |
| Missing cells | 80 |
| Distinct rows removed | 79 |
| Rows actually fitted and exported | 1,921 |
| Components | 12 |
| Retained standardized variance | about 99.718971736% |
| Rounded to one decimal for the resume | 99.7% |
| Output shape | 1,921 rows x 12 PC columns |

Why is retention so high? The generator intentionally creates 100 correlated
features from 12 latent factors plus modest noise. There is a low-dimensional
signal structure to recover. This is a demonstration, **not a representative
real-world dataset** and not evidence that 12 components will always be enough.

The number is never hard-coded in the API or charts. Run
`python scripts/benchmark.py` and inspect `artifacts/benchmark.json`.
`docs/benchmark.json` contains the saved verification run, input SHA-256,
package versions, ratios and independent check.

Do not say “99.7% accuracy,” “lossless compression” or “88% file-size savings.”
Reducing 100 feature dimensions to 12 is an 88% dimensional reduction, not
necessarily an 88% reduction in serialized CSV bytes or in downstream cost.

## 7. Why these preprocessing choices?

**Numeric selection:** text, identifiers parsed as strings, categorical data,
and mixed text/numeric columns are skipped and reported. The app does not
silently coerce arbitrary strings or one-hot encode categorical columns.
Numeric IDs or target-label columns can still be included if uploaded as
numbers; the user must remove them when inappropriate.

**Complete-case deletion:** a selected numeric row with NaN or infinity is
removed. This is simple and transparent, but can discard data and introduce
bias. Median/mean imputation is an alternative with its own assumptions.
Missing cells and removed rows are different quantities: 80 cells occur in
79 distinct rows in this benchmark.

**Constant columns:** removed after cleaning. They carry no variance.
If every numeric column is constant, the request is rejected instead of
returning NaN explained-variance values.

**Component limit:** the smaller of usable features and complete rows minus
one. Centering limits rank to at most `n-1`. Perfectly correlated features
can make the numerical rank lower still; some allowed later components can
then explain negligible variance. This is an upper bound, not a promise that
each component contains substantial information.

**Full SVD:** deterministic exact decomposition for this bounded demo. For
very large matrices, randomized PCA or IncrementalPCA could be considered.
Do not claim that full SVD is free, constant-time or the best choice at every scale.

**No whitening:** PC scores preserve the component variance ordering.
Whitening rescales scores to unit variance and would change their interpretation.

## 8. Explain the two endpoints and 11 failure classes

The two REST endpoints are `POST /api/analyze` and `GET /api/download`.
`/` serves the UI and `/sample_100d_data.csv` serves a static demo file;
they are not additional analysis API endpoints.

| Primary failure class | Error code | Status |
|---|---|---:|
| No upload field | MISSING_FILE | 400 |
| Empty upload filename | MISSING_FILENAME | 400 |
| Not a CSV filename | INVALID_FILE_TYPE | 415 |
| Missing/non-integer component value | INVALID_COMPONENTS | 400 |
| Component value below/above supported bound | COMPONENTS_OUT_OF_RANGE | 422 |
| Empty, malformed, non-UTF-8 or ambiguous-header CSV | INVALID_CSV | 400 |
| No numeric features | NO_NUMERIC_FEATURES | 422 |
| Fewer than two complete numeric rows | INSUFFICIENT_ROWS | 422 |
| No variable numeric features | ZERO_VARIANCE | 422 |
| Request above 50,000,000 bytes | UPLOAD_TOO_LARGE | 413 |
| Missing, invalid, unknown or expired download ID | RESULT_NOT_FOUND | 404 |

There are additional safeguards for parsed dataset size, unsafe numerical
results, oversized output and a busy server. “11 failure paths” means the
11 documented primary classes, not that there are only 11 tests or that every
possible error has been exhaustively handled.

The upload ceiling is decimal **50 MB for the whole multipart HTTP request**,
including boundaries and form fields. A file of exactly 50 MB is slightly too
large once wrapped in a request. There are independent row/column/cell caps.
The upload limit is not a promise that every 50 MB dataset will be accepted.

Client checks improve feedback. Server checks remain authoritative because
a caller can bypass the browser. An extension check is not a security scan:
the server also validates the CSV contents, format and numerical data.

## 9. “Async frontend” is not “async backend”

`fetch` returns a Promise. `await` suspends the function until the response
arrives while the browser can keep rendering. Loading states prevent duplicate
submissions and errors are presented without refreshing the page.

Flask/PCA work is synchronous and CPU-bound on the server. This rebuild
permits one active analysis per process and returns 429 to a concurrent
analysis. It does **not** implement a task queue, job polling, event streaming
or distributed processing.

## 10. Downloads, memory and security limitations

- Reduced CSV results use 192-bit random bearer IDs.
- Cache: up to 16 entries, 64 MiB total, nominal 15-minute TTL.
- Oldest results can be evicted before TTL; restart/redeploy clears everything.
- TTL cleanup is lazy on cache access; expired bytes are reclaimed on the next
  put/get/cache inspection, not by a background sweeper.
- A thread lock protects the cache; a lock does not make it multi-process.
- Gunicorn runs **one worker with two threads**. Multiple workers would each
  have a different cache and could fail downloads for another worker's result.
- Raw files are not saved by application code; multipart parsing may spool
  the request to a temporary file. Reduced results are still held server-side.
- No user accounts, per-user permissions, rate limiter or distributed storage.
- Do not upload confidential/personal datasets to this public demo.
- CSP and safe DOM text insertion reduce some frontend risks; “hardened”
  means the documented validation cases, not a penetration-tested service.

Production improvements would include authenticated ownership checks,
distributed or object-backed result storage, job workers and per-user quotas.
These are future improvements, not features to put on the current resume.

## 11. The five-minute interview demonstration

1. Open the app. Explain that empty-state numbers are not fabricated.
2. Click **Try the 100-feature sample**.
3. Show 100 numeric features, 12 PCs, about 99.72%, and 1,921 retained rows.
4. Switch between per-component and cumulative variance.
5. Expand the exact variance table and explain the sum.
6. Show 80 missing cells versus 79 rows dropped.
7. Expand component weights: PCs combine features rather than select them.
8. Download the CSV and show 12 PC columns and 1,921 rows.
9. Set components to 101 and show the server's bounds error.
10. Run `python -m pytest -q` and `python scripts/benchmark.py`.
11. Point to the independent covariance check, not just the UI number.

## 12. Experiments you should perform yourself

- Change components to 2, 6, 12 and 20; predict and explain the variance change.
- Try independent random features: 12 components should not retain 99.7%.
- Scale one input column by 1,000 and see why StandardScaler largely cancels it.
- Add a text column, constant column, empty numeric cell and infinite value.
- Reduce to one component and explain why its scores can be negative.
- Remove scaling in a local experiment and compare how unit changes affect PCA.
- Fit a downstream model on training data only. Learn why fitting scaling/PCA
  on train+test data leaks information into evaluation.
- Read each primary validation test and reproduce its request.

If you can do these and explain the trade-offs, you can showcase the project
credibly instead of relying on memorized resume language.