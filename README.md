# AWIP: Adaptive Workflow Intelligence Platform 🚀

<div align="center">
  <p><strong>The platform that does the data science so you don't have to.</strong></p>
  <p>An end-to-end autonomous data science orchestration engine.</p>
</div>

<br />

## 🔗 Live Demo
**Try it yourself:** [AWIP Live Platform](https://adaptive-workflow-intelligence-plat-kappa.vercel.app/)

## 🛑 Problem
Machine learning workflows involve repetitive, highly-technical boilerplate: cleaning missing data, encoding categorical variables, scaling features, tuning hyperparameters, and evaluating metrics. Data scientists spend hours on these routine tasks before generating actual insights.

## 💡 Solution
**AWIP automates the entire pipeline.** You upload a dataset, and AWIP's 7-Agent AI system autonomously cleans the data, engineers features, trains state-of-the-art models (XGBoost, LightGBM, RandomForest), explains the results, and generates a production-ready API and Jupyter Notebook for deployment.

## 💻 GitHub
The complete source code is available here: [GitHub Repository](https://github.com/Akshat1322/-Adaptive-Workflow-Intelligence-Platform)

---

## 📸 Platform Interface

<div align="center">
  <img src="docs/dashboard.png" alt="Upload Dashboard" width="800" style="border-radius: 8px; margin-bottom: 20px;" />
  <br />
  <img src="docs/overview.png" alt="Experiment Overview" width="800" style="border-radius: 8px; margin-bottom: 20px;" />
  <br />
  <img src="docs/results.png" alt="Model Results" width="800" style="border-radius: 8px;" />
</div>

---

## 🏗️ Architecture

```mermaid
graph TD
    A[Dataset Upload] --> B(Data Agent: Context)
    B --> C(Feature Agent: Imputing & Scaling)
    C --> D(Model Agent: Selection & Tuning)
    D --> E(Evaluation Agent: Metrics)
    E --> F(Explainability Agent: SHAP Values)
    F --> G(Reporting Agent: Gemini LLM Insights)
    
    A -.-> H((Knowledge Base: SQLite))
    H -.-> D
```

## 🛠️ Tech Stack

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue.svg?style=for-the-badge" alt="Python Version" />
  <img src="https://img.shields.io/badge/Next.js-14-black.svg?style=for-the-badge" alt="Next.js Version" />
  <img src="https://img.shields.io/badge/Google_Gemini-GenAI-orange.svg?style=for-the-badge" alt="AI Frameworks" />
</div>

<br />

- **Frontend:** Next.js 14, React, TailwindCSS, Zustand (Hosted on Vercel)
- **Backend:** FastAPI, Uvicorn, Python 3.12 (Hosted on Render)
- **Machine Learning:** Scikit-Learn, XGBoost, LightGBM, Pandas, Numpy
- **Generative AI:** Google Gemini GenAI SDK (`google-genai`)
- **Persistence:** SQLite via SQLAlchemy
