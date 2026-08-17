# PCA Dimension Reduction Pipeline

This project is a Flask web app for reducing high-dimensional CSV data with Principal Component Analysis (PCA). Upload a CSV, choose the number of components, and download the transformed dataset.

I built it as a simple end-to-end data preprocessing project. The backend handles cleaning, scaling, PCA, and CSV generation. The frontend shows the results without reloading the page.

## What it does

- Uploads CSV files up to 50 MB
- Uses only numeric columns for PCA
- Removes rows with missing or infinite numeric values
- Standardizes the data before PCA
- Lets the user choose the number of PCA components
- Shows processing time, row counts, feature counts, and retained variance
- Displays explained variance in a Chart.js chart
- Shows the first 10 rows of the transformed data
- Downloads the PCA output as a CSV file

## Built with

- Python, Flask, Pandas, NumPy, scikit-learn, and Werkzeug
- HTML, CSS, JavaScript, and Chart.js

## How the app works

```text
CSV upload
  → select numeric columns
  → clean missing/infinite values
  → StandardScaler
  → PCA
  → results in browser and CSV download
```

## Files

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

Running the generator creates `sample_100d_data.csv` in the project folder. It contains 2,000 rows and 100 correlated numeric features, with a small number of missing values for testing the cleaning step.

## Run locally

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate_sample_data.py
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser. Upload `sample_100d_data.csv`, set the components to `10`, and click **Run PCA**.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Opens the web app |
| POST | `/api/analyze` | Uploads and processes a CSV |
| GET | `/api/download?analysis_id=VALUE` | Downloads a completed PCA result |

Example request:

```bash
curl -s -X POST http://127.0.0.1:5000/api/analyze \
  -F "file=@sample_100d_data.csv" \
  -F "components=10"
```

Use the `analysis_id` from that response to download the result:

```bash
curl -L "http://127.0.0.1:5000/api/download?analysis_id=PASTE_ANALYSIS_ID_HERE" \
  -o pca_reduced_data.csv
```

## Quick checks

```bash
python -m py_compile app.py
python -m py_compile generate_sample_data.py
python generate_sample_data.py
```

With the Flask app running, these should return JSON responses:

```bash
curl -s -X POST http://127.0.0.1:5000/api/analyze -F "file=@sample_100d_data.csv" -F "components=10"
curl -s -X POST http://127.0.0.1:5000/api/analyze -F "file=@sample_100d_data.csv" -F "components=0"
curl -s -X POST http://127.0.0.1:5000/api/analyze -F "file=@README.md" -F "components=10"
```

## Push to GitHub

Run these commands only from the project folder:

```bash
git add .
git commit -m "Initial commit - PCA dimensionality reduction pipeline"
git branch -M main
git remote add origin https://github.com/tejashr0716/pca-dimension-reduction.git
git push -u origin main
```
