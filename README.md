# 📊 PCA Dimension Reduction Pipeline

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-2.x-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![Scikit--learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.x-FF6384?style=for-the-badge&logo=chart.js&logoColor=white)](https://www.chartjs.org/)

A Flask-based **data preprocessing and dimensionality reduction web application** that uses **Principal Component Analysis (PCA)** to transform high-dimensional CSV datasets into a smaller set of informative components.

The application provides an end-to-end workflow for uploading CSV data, validating and cleaning numeric features, standardizing the dataset, applying PCA, visualizing explained variance, and downloading the transformed dataset.

---

## 📌 Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [How the Application Works](#-how-the-application-works)
- [System Architecture](#-system-architecture)
- [PCA Processing Pipeline](#-pca-processing-pipeline)
- [Project Structure](#-project-structure)
- [Getting Started & Local Setup](#-getting-started--local-setup)
- [API Endpoint](#-api-endpoint)
- [Sample Dataset](#-sample-dataset)
- [Validation & Error Handling](#-validation--error-handling)
- [Quick Checks](#-quick-checks)
- [Author](#-author)

---

## 📖 Project Overview

High-dimensional datasets can contain hundreds of numerical features, increasing computational cost and making data analysis more difficult.

This project provides a simple web-based preprocessing pipeline that reduces dimensionality using **Principal Component Analysis (PCA)**.

The application performs the following operations:

1. Accepts a CSV file from the user.
2. Identifies numeric columns.
3. Removes rows containing missing or infinite numeric values.
4. Standardizes the numerical features using `StandardScaler`.
5. Applies PCA with a user-selected number of components.
6. Calculates explained and cumulative variance.
7. Displays processing statistics in the browser.
8. Visualizes explained variance using Chart.js.
9. Provides the transformed dataset as a downloadable CSV file.

The project demonstrates practical experience with **Flask API development, data preprocessing, NumPy/Pandas data handling, scikit-learn pipelines, and asynchronous frontend communication**.

---

## ✨ Key Features

- **📂 CSV Upload:** Upload datasets for dimensionality reduction.
- **🔢 Numeric Feature Selection:** Automatically selects numerical columns suitable for PCA.
- **🧹 Data Cleaning:** Removes rows containing missing or infinite numeric values.
- **📏 Feature Standardization:** Uses `StandardScaler` before PCA.
- **📉 Dimensionality Reduction:** Supports user-defined PCA component counts.
- **📊 Variance Analysis:** Calculates explained and cumulative explained variance.
- **📈 Visualization:** Displays explained variance using Chart.js.
- **⚡ Asynchronous Processing:** Sends analysis requests without requiring a full page reload.
- **📋 Result Preview:** Displays the first 10 rows of the transformed dataset.
- **⬇️ CSV Download:** Allows users to download PCA-transformed data.
- **⏱️ Processing Metrics:** Displays processing time and input/output dataset dimensions.
- **🛡️ Input Validation:** Validates uploaded files and PCA component values.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.10+, Flask |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | scikit-learn |
| **Preprocessing** | StandardScaler |
| **Dimensionality Reduction** | PCA |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Visualization** | Chart.js |
| **Server Utilities** | Werkzeug |
| **Testing / Validation** | Python compilation checks, API testing |
| **Environment & Tooling** | Python Virtual Environment, Git, GitHub |

---

## 🏗️ System Architecture

```text
pca-dimension-reduction/
├── app.py
├── generate_sample_data.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   └── index.html
│
└── static/
    └── style.css
