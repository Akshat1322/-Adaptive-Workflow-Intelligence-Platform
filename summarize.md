# AWIP — Adaptive Workflow Intelligence Platform
### Complete Project Summary · Written June 2026

---

## What Is This Project?

AWIP is an **AI-powered data science workspace**. The core idea: a user uploads any CSV dataset, and AWIP's AI team does what a skilled data scientist would do — inspects the data, detects problems, designs a machine learning pipeline, trains models, explains the results, and stores the knowledge for future use. All automatically.

Think of it as a **personal ML co-pilot** that replaces the tedious, repetitive manual work before actual modelling begins: the cleaning, the decision-making about which imputer to use, whether to apply SMOTE, what model fits this kind of data, why the pipeline looks the way it looks.

The project is **not** a chatbot. It is not a data dashboard. It is a full-stack AI system where a backend orchestrates a team of specialized agents and a frontend shows every step of that reasoning in real time.

---

## What It Actually Does — The Full Loop

Here is the exact sequence when a user uploads a dataset:

```
1. User uploads a CSV file
       ↓
2. Context Understanding Engine (CUE) analyzes it
   - Counts rows, columns, data types
   - Detects missing values (column-by-column ratios)
   - Detects outliers (Z-score based, σ > 3)
   - Checks class imbalance (majority/minority ratio)
   - Checks high cardinality in categoricals (> 50 unique)
   - Checks multicollinearity between numeric features (r > 0.9)
   - Infers domain from column names (healthcare, finance, HR, retail, etc.)
   - Infers ML task type (binary classification, multiclass, regression,
     time series, clustering, anomaly detection, NLP)
       ↓
3. Workflow Adaptation Engine (WAE) designs a pipeline DAG
   - Deterministic rule engine selects steps based on signals:
     • Missing values → KNNImputer or IterativeImputer
     • Categorical features → OrdinalEncoder or TargetEncoder
     • Outliers → RobustScaler; else → StandardScaler
     • High dimensionality → PCA(0.95 variance)
     • Class imbalance → SMOTE or SMOTE+Tomek
     • Task type + dataset size → XGBoost, LightGBM, RandomForest, Ridge, etc.
     • Explainability → SHAP (TreeExplainer for tree models)
   - LLM (via Ollama locally) generates a narrative explanation of each choice
       ↓
4. Pipeline Executor builds and runs the pipeline
   - Converts the DAG into an actual sklearn/imblearn Pipeline
   - Splits train/test (80/20, stratified where applicable)
   - Trains the primary model
   - Evaluates: accuracy, F1, precision, recall, AUC-ROC (classification)
     or RMSE, MAE, R² (regression)
   - Runs 5-fold cross-validation
   - Generates a leaderboard: trains 3-4 candidate models, ranks by score
   - Computes SHAP values for feature importance
       ↓
5. Specialized agents broadcast reasoning on a shared MessageBus
   - DataAgent: "Dataset analyzed. 3 missing columns detected."
   - FeatureAgent: "Engineered 4 lag features, applied SMOTE."
   - ModelAgent: "XGBoost wins leaderboard at 0.89 AUC."
   - EvaluationAgent: "F1 weak on class 2 — investigate minority samples."
   - ExplainabilityAgent: "Top SHAP feature: MonthlyIncome."
   - ReportingAgent: Compiles full markdown report.
   - DriftAgent: (on second upload) KS-test per column to detect drift.
   - DeploymentAgent + MonitoringAgent: Package model, flag monitoring status.
       ↓
6. Results stored in KnowledgeBase
   - Persisted to knowledge_base.json
   - Indexed in ChromaDB (local vector database) for semantic search
       ↓
7. Frontend shows everything in real time
   - Workflow DAG rendered as interactive node graph
   - Experiment leaderboard with live scores
   - Agent reasoning stream in the right panel (via SSE)
   - AI Copilot chat for natural language questions
   - Knowledge Base search over past experiments
   - Report Studio with markdown rendering and PDF/DOCX export
   - Drift Monitor when a second dataset is uploaded
```

---

## Architecture: Two Stacks, One Product

### Backend — FastAPI + Python ML
**Location:** `backend/`

| File / Module | What It Does |
|---|---|
| `main.py` | FastAPI app with all REST/SSE endpoints |
| `core/context_engine.py` | Dataset analysis → ContextSignals (337 lines of real statistical logic) |
| `core/workflow_engine.py` | Rule engine → WorkflowDAG. Deterministic pipeline design (517 lines) |
| `core/pipeline_executor.py` | WorkflowDAG → sklearn Pipeline → train, evaluate, SHAP (604 lines) |
| `core/llm_engine.py` | Interface to local Ollama for narrative reasoning + copilot chat |
| `core/knowledge_memory.py` | Experiment storage: JSON file + ChromaDB vector index |
| `core/intent_parser.py` | Parses natural language commands into intents (NAVIGATE, EXPLAIN, etc.) |
| `core/report_generator.py` | Generates PDF and DOCX reports from markdown |
| `core/visuals.py` | Plotly chart generators (DAG, experiment comparisons) — used by Streamlit |
| `core/agents/orchestrator.py` | Team lead. Sequences all agent phases, manages MessageBus |
| `core/agents/data.py` | Runs CUE, broadcasts dataset signals |
| `core/agents/feature.py` | Feature engineering: lag features, ratios, datetime extraction |
| `core/agents/model.py` | Selects winner from leaderboard, explains tradeoffs |
| `core/agents/evaluation.py` | Analyzes failure modes in evaluation metrics |
| `core/agents/explainability.py` | Interprets SHAP output, highlights key features |
| `core/agents/drift.py` | KS-test based distribution drift detection |
| `core/agents/research.py` | Suggests best practices based on task type and signals |
| `core/agents/reporting.py` | Composes executive markdown report |
| `core/agents/deployment.py` | Packages model for deployment |
| `core/agents/monitoring.py` | Flags monitoring status post-deployment |
| `database.py` | SQLAlchemy stub (not yet used in production paths) |

**Key API Endpoints:**

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/upload` | POST | Upload CSV, run CUE, return signals |
| `/api/orchestrate` | POST | Full blocking orchestration, return results |
| `/api/orchestrate/stream` | GET | SSE stream of agent messages + final result |
| `/api/datasets` | GET | Session dataset history |
| `/api/drift/compare` | GET | KS-test drift between previous and current dataset |
| `/api/chat` | POST | Natural language command → LLM response |
| `/api/knowledge` | GET | All stored experiments |
| `/api/knowledge/search` | POST | Semantic search over ChromaDB |
| `/api/report/generate` | POST | Generate markdown report |
| `/api/report/export/{fmt}` | GET | Download PDF or DOCX |
| `/api/feed` | GET | All agent messages from last orchestration |

### Frontend — Next.js + React + Zustand
**Location:** `frontend/`

| File | What It Does |
|---|---|
| `src/app/page.tsx` | Main workspace page: layout, upload, SSE streaming, autonomy mode |
| `src/store/workspaceStore.ts` | Zustand global state: workflow, leaderboard, messages, chat, report |
| `src/lib/orchestration.ts` | Shared SSE streaming helper, reused by rerun/improve |
| `src/components/DatasetIntelligence.tsx` | Dataset upload, row/col/task metrics, autonomy toggle |
| `src/components/InteractiveDAG.tsx` | Real workflow steps rendered as interactive node graph |
| `src/components/ExperimentLab.tsx` | Real leaderboard scores, model comparison chart |
| `src/components/AgentFeed.tsx` | Live agent activity stream from SSE |
| `src/components/AgentCollaboration.tsx` | Reads shared agent message store |
| `src/components/CommandPalette.tsx` | Ctrl+K command bar: navigate, trigger orchestration, chat |
| `src/components/KnowledgeBase.tsx` | Semantic search UI over past experiments |
| `src/components/ReportStudio.tsx` | Render markdown report, export PDF/DOCX |
| `src/components/DriftMonitor.tsx` | Dataset history, drift scores, drifted features |
| `src/components/ReasoningTimeline.tsx` | Timeline view of agent reasoning steps |
| `src/components/Skeleton.tsx` | Loading skeleton placeholders |
| `src/components/ToastContainer.tsx` | Error/success toast notifications |

**Also exists:** `app.py` — a legacy Streamlit version of the app. It is still functional and was the original single-file UI. It shares the same backend core modules but does not use the FastAPI server. Left in for reference.

### State Management

All frontend components share a **Zustand store** (`workspaceStore.ts`). When orchestration completes (streaming or blocking), one `applyOrchestrationResult()` call updates the entire workspace: DAG, leaderboard, agent messages, report, and metrics. Every panel re-renders automatically with real data.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) |
| ML Pipeline | scikit-learn, XGBoost, LightGBM, imbalanced-learn |
| Explainability | SHAP (TreeExplainer / KernelExplainer) |
| Statistics | SciPy (KS-test, Z-score) |
| LLM Integration | Ollama (local, privacy-preserving) — llama3 or phi-3 |
| Vector Search | ChromaDB (local persistent) |
| Data | Pandas, NumPy |
| Report Export | FPDF (PDF), python-docx (DOCX) |
| Frontend | Next.js 15, React, TypeScript |
| State | Zustand |
| Real-time | Server-Sent Events (SSE) |
| Legacy UI | Streamlit (app.py, still functional) |
| Visualization | Plotly (backend), React (frontend) |

---

## Key Features for Users Who Want Automation

This is where AWIP has genuine value for someone trying to automate their ML work:

1. **Zero-configuration ML** — Upload a CSV, pick a target column. The system decides everything else: what to clean, what model to use, what to explain. No coding required.

2. **Adaptive pipeline design** — It doesn't apply a fixed template. It inspects your data and adapts. Imbalanced classes? SMOTE gets added automatically. Outliers? RobustScaler replaces StandardScaler. High cardinality categoricals? TargetEncoder instead of OHE. This happens silently, correctly, every time.

3. **Drift detection on update** — Upload a new version of your dataset. AWIP compares it to the previous one using KS-tests and tells you which features have shifted distribution. This matters for production ML where data changes over time.

4. **Persistent knowledge** — Every experiment is stored. Search across past runs: "What worked for HR classification?" The ChromaDB-backed semantic search finds relevant past experiments and surfaces the insight.

5. **Autonomy Mode** — Toggle it on, upload a dataset, and orchestration starts automatically without any button clicks. End goal: fully automated data science on dataset arrival.

6. **Exportable reports** — Generate PDF or DOCX executive summaries from the Report Studio. No manual writing.

7. **Reproducible code** — The pipeline executor can output the exact Python code that replicates whatever sklearn pipeline it built. Copy-paste and run.

---

## What a User Should Actually Expect

**You get:**
- A real ML pipeline trained on your data in under 60 seconds for small/medium datasets
- A visual workflow DAG that shows exactly what steps were taken and why
- A leaderboard of 3-4 models compared on your task
- SHAP-based feature importance for the winning model
- Live agent reasoning stream so you can watch the AI team work
- A searchable history of all your past experiments
- A downloadable executive report
- Basic drift detection between dataset versions

**You don't get (yet):**
- Hyperparameter tuning (it uses reasonable but fixed params)
- Deep learning support
- SQL/database connectors (CSV only)
- Multi-user workspaces (session is in-memory on the server)
- Deployment to actual infrastructure
- Iterative refinement via chat (chat exists but "improve recall" won't re-run with modified params yet)

**Requirements to run:**
- Python 3.9+ with dependencies installed (`requirements.txt`)
- [Ollama](https://ollama.com/) running locally with llama3 or phi-3 (for LLM features)
- Node.js for the Next.js frontend

**How to start:**
```bash
# Terminal 1 — Backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev

# Then open http://localhost:3000
```

Or use `start.bat` if it matches your local environment.

---
---

# ⚠ WHAT IT SHOULD HAVE BEEN
## A Brutally Honest Section

Let's stop pretending and say the uncomfortable thing out loud.

---

### The Vision Was Right. The Execution Got Lost.

The idea behind AWIP is genuinely good and ahead of its time: an AI agent team that inspects data, reasons about it, builds a pipeline, and explains every decision — without the user writing a single line of code. That is a real problem. That is something people would pay for.

But the execution drifted far from that core promise. Here is exactly how:

---

### 1. It became a feature showcase, not a product.

At some point, the development shifted from "make this one loop work perfectly" to "add more things." Drift monitoring, deployment agents, monitoring agents, research agents, reporting agents, ChromaDB, PDF export, SSE streaming, Streamlit AND Next.js — all added in parallel, none of them finished.

**What it should have been:** One loop. Upload → Analyze → Pipeline → Results → Explain. Made airtight, beautiful, and fast. *Then* drift. *Then* reports. Not all at once.

A product that does one thing excellently is infinitely more valuable than a platform that does ten things at 60%.

---

### 2. The frontend was theater for too long.

For a substantial part of this project's life, every single component on the frontend showed hardcoded fake data. The "Experiment Lab" showed 4 static made-up experiments. The "Knowledge Base" showed 2 made-up cards. The DAG showed 5 hardcoded nodes. The ReasoningTimeline was frozen.

Meanwhile, the backend was doing real, sophisticated work. Real KS-tests. Real SHAP values. Real cross-validation leaderboards.

**What it should have been:** Backend and frontend wired together from day one. No component ships with mock data. If the data isn't there yet, show an empty state with a clear call to action. Empty is honest. Mock data is a lie that makes bugs invisible.

This gap was eventually closed, but it burned weeks of time and created the impression — even to the person building it — that the system was more functional than it was.

---

### 3. Two UIs is one UI too many.

The project has `app.py` (Streamlit) AND a full Next.js frontend. Both share the same backend Python modules. Both are partially functional. Neither is complete.

**What it should have been:** Pick one UI and ship it. The Next.js frontend is clearly the right long-term bet. The Streamlit app was fine as a prototype to validate the backend. It should have been retired the moment the Next.js frontend started.

Having two UIs means every feature must be built twice or not built at all. The README still tells users to run `streamlit run app.py`. The actual product runs on `npm run dev`. This is confusing and unprofessional.

---

### 4. The agent team is mostly decorative.

There are 10 agents: Orchestrator, Data, Feature, Model, Evaluation, Explainability, Drift, Research, Deployment, Monitoring, Reporting.

Exactly 3 of them do real, substantive work:
- **DataAgent**: Calls CUE to produce actual signals.
- **FeatureAgent**: Does some real feature engineering.
- **PipelineExecutor** (not even an agent, called by Orchestrator): Does the real ML work.

The rest — Research, Deployment, Monitoring, Reporting — largely generate placeholder text or perform superficial actions. The ResearchAgent's "insights" are canned strings. The DeploymentAgent returns a dict saying deployment is "pending." The MonitoringAgent checks if a model exists.

**What it should have been:** Two or three agents that do real, deep work. Not ten agents that broadcast-announce work they aren't actually doing.

The MessageBus pattern and the BaseAgent architecture are genuinely good ideas. They should have been applied to 3 honest agents rather than stretched over 10 hollow ones.

---

### 5. The LLM integration is fragile and largely cosmetic.

The LLM (via Ollama) is called to generate "reasoning" about why a workflow step was chosen. But if Ollama is not running — which is often the case for new users — the whole LLM path fails silently and falls back to template strings. The fallback strings are often better than what Ollama generates anyway.

**What it should have been:** Decide early whether LLM is core or optional. If core: require it, document it hard, fail loudly and helpfully when it's missing. If optional: make the rule-based explanations excellent on their own and treat LLM as an enhancement that adds depth, not the main show.

Right now it is neither. It is a partially-wired dependency that creates confusion about whether the app "needs AI" to work.

---

### 6. Session state in memory is a time bomb.

The backend stores everything — the uploaded dataframe, the previous dataframe for drift, the workflow results, the agent messages — in a global Python dictionary (`session_state`). Restart the server: everything is gone. Two users open the app simultaneously: they share and overwrite each other's state.

**What it should have been:** From the moment a second HTTP endpoint was added, the session state should have moved to a real store — Redis for in-memory, SQLite/Postgres for persistence. The KnowledgeBase got this right (JSON file + ChromaDB). The rest of the session didn't.

This is not a "nice to have later" issue. It is a fundamental architectural flaw that makes the app single-user-only and unreliable. A server crash between upload and orchestration loses the user's dataset entirely.

---

### 7. The automation promise is half-delivered.

The project description says "automate everything." The Autonomy Mode toggle exists. When on, upload triggers orchestration automatically.

But what happens next requires the user to:
- Manually check the DAG
- Manually read the leaderboard
- Manually go to the Report Studio and click Generate
- Manually click Export

True automation would mean: dataset arrives → pipeline runs → report is generated → report is emailed or saved → user is notified. The only thing automated is the trigger. Everything after is still manual.

**What it should have been:** Define what "automated" means to the user and build that end-to-end. If it means "I drop a CSV and get a PDF report with no further clicks," build that exact loop. A webhook that accepts a CSV, runs the full pipeline, and emails back a PDF would be more genuinely automated than any amount of UI polish.

---

### What a User Should Realistically Expect

If you are evaluating this project hoping it will automate your data science work:

**It will:** Correctly identify your ML task type, design a sensible pipeline, train a real model, and show you feature importances. If your dataset is a standard CSV with a clear target column, it will produce a useful baseline model with zero configuration.

**It won't:** Replace a data scientist. The pipeline choices are good defaults, not expert selections. It doesn't tune hyperparameters. It doesn't handle images, audio, or unstructured data. It doesn't integrate with your data warehouse. It won't monitor a deployed model in production. The "deployment" and "monitoring" agents are stubs.

**The honest pitch:** AWIP is a very good, very ambitious prototype of what an autonomous ML co-pilot could be. It is not that co-pilot yet. It is closer than most comparable open-source projects. But there is a meaningful gap between what it shows and what it does — and a user who expects full automation will hit that gap quickly.

---

### The Real Opportunity

Despite all of this — the project has a genuinely differentiated core:

The **ContextUnderstandingEngine** + **WorkflowAdaptationEngine** combination is the real product. The idea that a system can inspect a dataset, understand its statistical properties, and design a correct, justified ML pipeline without human intervention — and explain every decision in plain language — that is not common. That is valuable. That is the thing to double down on.

Everything else — the agents, the UI, the reports, the drift monitor — is scaffolding around that core insight.

**Stop building rooms. Wire up the ones you have. And then make the core loop so good that it sells itself.**

---

*Summary written June 2026 — based on full codebase review of AWIP v3.*
