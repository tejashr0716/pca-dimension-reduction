# PCA Dimensionality Reduction Pipeline

A Flask web application that uploads a CSV, cleans numeric data, standardizes features, runs PCA, visualizes explained variance, previews transformed data, and downloads the reduced CSV.

## Features

- CSV upload up to 50 MB
- Automatic numeric-column selection
- Vectorized NaN and infinity cleaning
- StandardScaler preprocessing and PCA component selection
- Metrics, explained-variance chart, and transformed-data preview
- Reduced CSV download without a page refresh
- Generated 2,000-row, 100-feature correlated sample dataset

## Technologies

- Python 3, Flask, NumPy, Pandas, scikit-learn, Werkzeug
- HTML5, CSS3, vanilla JavaScript, Chart.js

## Architecture

`CSV upload → Pandas numeric selection → NaN/infinity cleaning → StandardScaler → PCA → JSON response / CSV download`

## Project structure

```text
pca-dimension-reduction/
├── app.py
├── generate_sample_data.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   └── index.html
└── static/
    └── style.css
```

`sample_100d_data.csv` is generated in the project root after running the sample-data command.

## Installation and running

```bash
python3 --version
cd pca-dimension-reduction
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate_sample_data.py
python app.py
```

Open `http://127.0.0.1:5000` in a browser.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Web interface |
| POST | `/api/analyze` | Upload and transform a CSV |
| GET | `/api/download?analysis_id=VALUE` | Download a completed transformation |

## Example API request

```bash
curl -s -X POST http://127.0.0.1:5000/api/analyze \
  -F "file=@sample_100d_data.csv" \
  -F "components=10"
```

Copy `analysis_id` from the JSON response, then run:

```bash
curl -L "http://127.0.0.1:5000/api/download?analysis_id=PASTE_ANALYSIS_ID_HERE" \
  -o pca_reduced_data.csv
```

## Testing

```bash
python -m py_compile app.py
python -m py_compile generate_sample_data.py
python generate_sample_data.py
python app.py
```

In a second terminal with the virtual environment activated:

```bash
curl -s -X POST http://127.0.0.1:5000/api/analyze -F "file=@sample_100d_data.csv" -F "components=10"
curl -s -X POST http://127.0.0.1:5000/api/analyze -F "file=@sample_100d_data.csv" -F "components=0"
curl -s -X POST http://127.0.0.1:5000/api/analyze -F "file=@README.md" -F "components=10"
```

## GitHub upload

```bash
git init
git add .
git commit -m "Initial commit - PCA dimensionality reduction pipeline"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pca-dimension-reduction.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username in the `git remote add origin` command.
