# AWIP (Adaptive Workflow Intelligence Platform)

> **"The platform that does the data science so you don't have to."**

AWIP is an end-to-end, multi-agent Data Science pipeline built on FastAPI and Next.js. It takes a raw CSV and outputs a fully trained machine learning model, a statistical breakdown of the dataset, and an executive PDF report — completely autonomously.

## 🚀 The Core Philosophy
Data scientists spend 80% of their time on data cleaning, imputation, and feature engineering. AWIP automates this drudgery. It's not a conversational chatbot; it's an **execution engine**. 

1. **Upload a CSV.**
2. **AWIP analyzes it (missing values, class imbalance, outliers).**
3. **AWIP designs a custom scikit-learn pipeline.**
4. **AWIP trains XGBoost, LightGBM, and Random Forest.**
5. **AWIP selects the winner and explains *why*.**
6. **You download the PDF report.**

---

## 🧠 Architecture

AWIP relies on a **7-Agent AI Team** directed by an Orchestrator. The LLM (Ollama) is entirely **optional** — the system runs flawlessly on intelligent rule-based heuristics. When Ollama is available, it enhances explanations, but it is never a bottleneck.

### The Agent Team
- **Data Agent:** Runs the Context Understanding Engine (CUE). Identifies data types, missing values, outliers, and class imbalances.
- **Feature Agent:** Handles imputation, scaling, and correlation-based feature filtering.
- **Model Agent:** Benchmarks multiple algorithms (XGBoost, LightGBM, Random Forest, Ridge) and selects the best performer.
- **Evaluation Agent:** Generates confusion matrices, classification reports, and identifies failure modes.
- **Explainability Agent:** Computes SHAP values to explain feature importance.
- **Drift Agent:** Compares current uploads to previous uploads to detect data drift using Kolmogorov-Smirnov tests.
- **Reporting Agent:** Synthesizes the entire pipeline into a downloadable PDF/DOCX Executive Report.

### Persistent Memory
AWIP uses **SQLite (via SQLAlchemy)** for session persistence. Datasets, workflow DAGs, and results survive server restarts.
Past runs are saved automatically as **Experiments** in a ChromaDB-backed **Knowledge Base**, allowing semantic search across your historical data science projects.

---

## ⚡ The `/api/orchestrate/auto` Endpoint
AWIP's crown jewel is its true automation endpoint.
You can POST a CSV file to this endpoint and receive a fully formatted PDF report in return. No clicks required.

```bash
curl -X POST "http://localhost:8000/api/orchestrate/auto" \
     -H "accept: application/pdf" \
     -F "file=@my_dataset.csv" \
     -o output_report.pdf
```
*Behind the scenes, this triggers: Analysis → Workflow → Training → Leaderboard → SHAP → Report Generation → Experiment Save → PDF Export.*

---

## 🛠️ Tech Stack
- **Backend:** FastAPI, Python, SQLAlchemy, scikit-learn, XGBoost, LightGBM, SHAP.
- **Frontend:** Next.js 14, React, TailwindCSS, Framer Motion, Zustand.
- **Database:** SQLite (Relational), ChromaDB (Vector Store).
- **LLM:** Ollama (Optional, runs locally).

---

## 💡 Suggestions for Next Steps

1. **Production Deployment:** Containerize the backend and frontend into a single `docker-compose.yml`. Swap SQLite for PostgreSQL for multi-user support.
2. **Model Export:** Add a button to download the trained `scikit-learn` pipeline as a `.pkl` file so users can deploy the winning model immediately.
3. **Custom Metrics:** Allow users to specify a target metric (e.g., prioritize Recall over Accuracy for fraud detection) during the upload phase.
