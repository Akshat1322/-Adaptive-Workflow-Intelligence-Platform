from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Callable
from dataclasses import asdict, is_dataclass
import os
import sys
import asyncio
import queue
import threading
import pandas as pd
import json
import numpy as np
import io
from datetime import datetime

# Add backend directory to sys.path so core modules can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agents.orchestrator import OrchestratorAgent
from core.agents.data import DataAgent
from core.agents.base import MessageBus
from core.knowledge_memory import KnowledgeBase
from core.intent_parser import IntentParser
from core.llm_engine import LLMEngine
from database import SessionLocal, DBSessionState

app = FastAPI(title="AWIP AI Data Science Workspace API", version="4.0.0")

# CORS config to allow Next.js frontend (default port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://[::1]:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── SESSION MANAGER ─────────────────────────────────────────────
# Replaces the old global session_state dict with SQLite persistence.

class SessionManager:
    """SQLite-backed session state. Survives server restarts."""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {
            "df": None,
            "previous_df": None,
            "dataset_name": None,
            "datasets": [],
            "workflow": None,
            "signals": None,
            "results": None,
            "agent_messages": [],
            "engineered_features": [],
            "report_markdown": None,
            "quality_score": None,
            "quality_issues": [],
        }
        self._load_from_db()
    
    def _load_from_db(self):
        """Load last session state from SQLite on server startup."""
        db = SessionLocal()
        try:
            row = db.query(DBSessionState).filter_by(session_key="default").first()
            if row:
                if row.dataset_csv:
                    try:
                        self._cache["df"] = pd.read_csv(io.StringIO(row.dataset_csv))
                    except Exception:
                        pass
                if row.previous_dataset_csv:
                    try:
                        self._cache["previous_df"] = pd.read_csv(io.StringIO(row.previous_dataset_csv))
                    except Exception:
                        pass
                self._cache["dataset_name"] = row.dataset_name
                self._cache["datasets"] = row.datasets_json or []
                self._cache["report_markdown"] = row.report_markdown
                self._cache["quality_score"] = row.quality_score
                self._cache["quality_issues"] = row.quality_issues or []
                # Note: signals, workflow, results are dataclass-based objects 
                # that need the orchestration to re-run. We persist the raw data
                # so the user can re-run from the last upload without re-uploading.
        finally:
            db.close()
    
    def _persist(self):
        """Write current cache to SQLite."""
        db = SessionLocal()
        try:
            row = db.query(DBSessionState).filter_by(session_key="default").first()
            if not row:
                row = DBSessionState(session_key="default")
                db.add(row)
            
            row.dataset_name = self._cache.get("dataset_name")
            
            df = self._cache.get("df")
            if df is not None:
                row.dataset_csv = df.to_csv(index=False)
            
            prev_df = self._cache.get("previous_df")
            if prev_df is not None:
                row.previous_dataset_csv = prev_df.to_csv(index=False)
            
            row.datasets_json = self._cache.get("datasets", [])
            row.report_markdown = self._cache.get("report_markdown")
            row.quality_score = self._cache.get("quality_score")
            row.quality_issues = self._cache.get("quality_issues", [])
            row.updated_at = datetime.utcnow()
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[SessionManager] Persist error: {e}")
        finally:
            db.close()
    
    def __getitem__(self, key: str):
        return self._cache[key]
    
    def __setitem__(self, key: str, value):
        self._cache[key] = value
    
    def get(self, key: str, default=None):
        return self._cache.get(key, default)
    
    def save(self):
        """Explicitly persist to disk. Call after mutations."""
        self._persist()


session_state = SessionManager()
knowledge_base = KnowledgeBase()
intent_parser = IntentParser()

class CommandRequest(BaseModel):
    command: str

class SearchRequest(BaseModel):
    query: str

def _message_to_dict(m) -> Dict[str, Any]:
    return {
        "sender": m.sender,
        "recipient": getattr(m, "recipient", "All"),
        "content": m.content,
        "timestamp": m.timestamp,
        "confidence": m.confidence,
        "metadata": _json_safe(m.metadata),
    }

def _json_safe(value):
    """Convert numpy/pandas values into plain JSON-serializable Python types."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return [_json_safe(v) for v in value.tolist()]
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value

def _resolve_target_col(df: pd.DataFrame, target_col: Optional[str]) -> str:
    if target_col:
        return target_col
    target_candidates = [
        c for c in df.columns
        if df[c].nunique() < 20 or c.lower() in ["target", "label", "churn"]
    ]
    if not target_candidates:
        target_candidates = list(df.columns)[:4]
    return target_candidates[0] if target_candidates else df.columns[0]

def _calculate_quality_score(signals) -> tuple:
    """Calculate a 0-100 data quality score from context signals."""
    score = 100.0
    issues = []
    
    if signals.has_missing_values:
        max_miss = max(signals.missing_columns.values()) if signals.missing_columns else 0
        penalty = min(30, max_miss * 100)
        score -= penalty
        issues.append(f"Missing values detected (up to {max_miss:.0%} in a column)")
        
    if signals.is_imbalanced:
        score -= 15
        issues.append(f"Severe class imbalance ({signals.imbalance_ratio:.1f}:1)")
        
    if signals.has_outliers:
        score -= 5
        issues.append(f"Outliers detected in {len(signals.outlier_columns)} columns")
        
    if signals.has_multicollinearity:
        score -= 5
        issues.append(f"Multicollinearity ({len(signals.multicollinear_pairs)} correlated pairs)")
        
    if signals.task_type == "unknown":
        score -= 20
        issues.append("Unable to determine task type reliably")
        
    if signals.is_high_dimensional:
        issues.append(f"High dimensionality ({signals.n_cols} features) increases overfitting risk")
        
    return max(0.0, score), issues


def _execute_orchestration(
    target_col: Optional[str] = None,
    on_message: Optional[Callable] = None,
) -> Dict[str, Any]:
    """Run the full orchestration pipeline and persist session state."""
    if session_state["df"] is None:
        return {"error": "No dataset uploaded"}

    df = session_state["df"]
    resolved_target = _resolve_target_col(df, target_col)

    message_bus = None
    orchestrator = OrchestratorAgent()
    if on_message:
        message_bus = orchestrator.message_bus
        message_bus.subscribe(on_message)

    loop_results = orchestrator.run_iterative_loop(
        session_state["df"],
        resolved_target,
        session_state["previous_df"],
        domain_hint="auto-detect",
    )

    signals = loop_results["signals"]
    results = loop_results["results"]
    workflow = loop_results["workflow"]
    features = loop_results["engineered_features"]
    report = loop_results.get("report", {})

    session_state["signals"] = signals
    session_state["engineered_features"] = features
    session_state["workflow"] = workflow
    session_state["results"] = results
    session_state["agent_messages"] = orchestrator.message_bus.get_all()
    session_state["report_markdown"] = report.get("markdown")

    winner_model = (
        next((s.name for s in workflow.steps if s.category == "model"), "Unknown")
        if workflow else "Unknown"
    )
    metrics = results.get("metrics", {}) if results else {}
    score = metrics.get("accuracy", metrics.get("r2_score", 0.0))

    # Save as numbered experiment in knowledge base
    knowledge_base.add_experiment(
        dataset_name=session_state["dataset_name"] or "Uploaded Dataset",
        task_type=signals.task_type,
        domain=getattr(signals, "domain_hint", "auto-detect"),
        winner_model=winner_model,
        score=score,
        features_added=len(features),
        key_issues=getattr(signals, "quality_issues", []) or [],
    )

    # Persist to SQLite
    session_state.save()

    workflow_dict = workflow.to_dict() if workflow else None

    return _json_safe({
        "status": "success",
        "workflow": workflow_dict,
        "results": metrics,
        "leaderboard": results.get("leaderboard", []) if results else [],
        "report": session_state["report_markdown"],
        "messages": [_message_to_dict(m) for m in session_state["agent_messages"]],
        "experiment_id": knowledge_base.get_experiment_count(),
    })


# ── ENDPOINTS ───────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"status": "AWIP Backend Running", "version": "4.0.0"}

@app.get("/api/status")
def get_status():
    """Reports system health including Ollama availability."""
    ollama_available = LLMEngine.check_available()
    exp_count = knowledge_base.get_experiment_count()
    has_dataset = session_state["df"] is not None
    return {
        "backend": "running",
        "ollama": "connected" if ollama_available else "unavailable",
        "experiments": exp_count,
        "dataset_loaded": has_dataset,
        "dataset_name": session_state["dataset_name"],
    }


@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Uploads a dataset, runs CUE analysis, returns signals + quality score."""
    content = await file.read()
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(content)
        
    try:
        df = pd.read_csv(temp_path)
        if session_state["df"] is not None:
            session_state["previous_df"] = session_state["df"].copy()
        session_state["df"] = df
        session_state["dataset_name"] = file.filename
        
        # Run CUE analysis
        from core.context_engine import ContextUnderstandingEngine
        cue = ContextUnderstandingEngine()
        signals = cue.analyze(df, target_column=None, user_intent="", domain_hint="auto-detect")
        session_state["signals"] = signals
        
        # Calculate real quality score
        quality_score, quality_issues = _calculate_quality_score(signals)
        session_state["quality_score"] = quality_score
        session_state["quality_issues"] = quality_issues
        
        dataset_record = {
            "name": file.filename,
            "rows": int(signals.n_rows),
            "cols": int(signals.n_cols),
            "task_type": signals.task_type,
            "uploaded_at": datetime.now().isoformat(),
        }
        datasets = session_state["datasets"] or []
        datasets.append(dataset_record)
        session_state["datasets"] = datasets

        # Persist to SQLite
        session_state.save()

        return {
            "status": "success", 
            "dataset": file.filename, 
            "rows": signals.n_rows,
            "cols": signals.n_cols,
            "task_type": signals.task_type,
            "quality_score": quality_score,
            "quality_issues": quality_issues,
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/orchestrate")
def orchestrate_pipeline(target_col: Optional[str] = Form(None)):
    """Runs the AI Data Science team orchestrator (blocking)."""
    return _execute_orchestration(target_col)

@app.get("/api/datasets")
def list_datasets():
    """Returns uploaded dataset history for the current workspace session."""
    return {"datasets": session_state["datasets"] or [], "active": session_state["dataset_name"]}

@app.get("/api/drift/compare")
def compare_drift():
    """Compare the current uploaded dataset with the previous uploaded dataset."""
    if session_state["previous_df"] is None or session_state["df"] is None:
        return {"status": "insufficient_data", "message": "Upload at least two datasets to compare drift."}

    from core.agents.drift import DriftAgent
    from core.agents.base import MessageBus

    old_df = session_state["previous_df"]
    new_df = session_state["df"]
    numeric_columns = list(set(old_df.select_dtypes(include="number").columns) & set(new_df.select_dtypes(include="number").columns))
    result = DriftAgent(MessageBus()).execute(old_df, new_df, numeric_columns)
    return _json_safe({"status": "success", **result, "numeric_columns": numeric_columns})

@app.get("/api/orchestrate/stream")
async def stream_orchestrate(target_col: Optional[str] = None):
    """SSE stream of agent messages during orchestration, then final result."""
    if session_state["df"] is None:
        async def error_stream():
            yield f"event: error\ndata: {json.dumps({'error': 'No dataset uploaded'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    event_queue: queue.Queue = queue.Queue()

    def on_message(msg):
        event_queue.put(("agent_message", _message_to_dict(msg)))

    def run_pipeline():
        try:
            result = _execute_orchestration(target_col, on_message=on_message)
            event_queue.put(("complete", result))
        except Exception as exc:
            event_queue.put(("error", {"error": str(exc)}))

    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()

    async def event_generator():
        yield f"event: started\ndata: {json.dumps({'status': 'orchestrating'})}\n\n"
        while True:
            try:
                event_type, payload = await asyncio.to_thread(event_queue.get, True, 180)
            except queue.Empty:
                yield f"event: error\ndata: {json.dumps({'error': 'Orchestration timed out'})}\n\n"
                break

            if event_type == "agent_message":
                yield f"event: agent_message\ndata: {json.dumps(payload)}\n\n"
            elif event_type == "complete":
                if payload.get("error"):
                    yield f"event: error\ndata: {json.dumps(payload)}\n\n"
                else:
                    yield f"event: complete\ndata: {json.dumps(payload)}\n\n"
                break
            elif event_type == "error":
                yield f"event: error\ndata: {json.dumps(payload)}\n\n"
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/orchestrate/auto")
async def auto_orchestrate(file: UploadFile = File(...), target_col: Optional[str] = Form(None), fmt: str = Form("pdf")):
    """Full automation endpoint: CSV in → Analysis → Workflow → Training → 
    Leaderboard → SHAP → Executive Report → PDF/DOCX out.
    
    Everything is saved as a numbered Experiment automatically.
    
    Pipeline:
      1. Upload & analyze dataset (CUE)
      2. Run full orchestration (Data → Feature → Workflow → Train → Model → Eval → SHAP → Report)
      3. Save as Experiment #N in knowledge base
      4. Export report as PDF or DOCX
      5. Return the file
    """
    if fmt not in {"pdf", "docx"}:
        fmt = "pdf"
    
    # Step 1: Upload and analyze
    content = await file.read()
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(content)
    
    try:
        df = pd.read_csv(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    if session_state["df"] is not None:
        session_state["previous_df"] = session_state["df"].copy()
    session_state["df"] = df
    session_state["dataset_name"] = file.filename
    
    # Step 2: Full orchestration (this calls all 7 agents + saves experiment)
    result = _execute_orchestration(target_col)
    
    if result.get("error"):
        return result
    
    # Step 3: Export report
    report_md = session_state["report_markdown"]
    if not report_md:
        report_md = f"# Experiment Report\n\nDataset: {file.filename}\n\nNo report generated."
    
    from core.report_generator import ReportGenerator
    
    exp_num = knowledge_base.get_experiment_count()
    filename = f"AWIP_Experiment_{exp_num}.{fmt}"
    output_path = os.path.join(os.getcwd(), filename)
    
    if fmt == "pdf":
        ReportGenerator.to_pdf(report_md, output_path)
        media_type = "application/pdf"
    else:
        ReportGenerator.to_docx(report_md, output_path)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    # Persist session
    session_state.save()
    
    return FileResponse(output_path, filename=filename, media_type=media_type)


@app.get("/api/feed")
def get_agent_feed():
    """Returns the live agent activity feed."""
    msgs = session_state["agent_messages"] or []
    return {"messages": [_message_to_dict(m) for m in msgs]}

@app.post("/api/chat")
def chat_command(req: CommandRequest):
    """Processes natural language commands."""
    intent_res = intent_parser.parse_intent(req.command)
    
    llm = LLMEngine()
    resp = llm.chat_with_context(
        req.command, 
        session_state["workflow"], 
        session_state["signals"], 
        session_state["results"],
        knowledge_base=knowledge_base,
        agent_messages=session_state["agent_messages"] or []
    )
    
    return {
        "intent": intent_res.get("intent"),
        "response": resp
    }

@app.get("/api/knowledge")
def get_knowledge():
    """Retrieves all past experiments."""
    experiments = knowledge_base.get_experiments()
    return {
        "experiments": experiments,
        "cards": [knowledge_base._experiment_to_card(exp, 100) for exp in experiments],
    }

@app.post("/api/knowledge/search")
def search_knowledge(req: SearchRequest):
    """Semantic search over past experiments using ChromaDB."""
    results = knowledge_base.search_experiments(req.query, n_results=5)
    return {"results": results}

@app.post("/api/report/generate")
def generate_report():
    """Generates an executive report from the current workspace session."""
    if session_state["results"] is None or session_state["signals"] is None:
        return {"error": "Run orchestration first to generate a report."}

    if session_state["report_markdown"]:
        return {"status": "success", "markdown": session_state["report_markdown"]}

    from core.agents.reporting import ReportingAgent
    from core.agents.base import MessageBus

    report_data = ReportingAgent(MessageBus()).execute(
        dataset_name=session_state["dataset_name"] or "Uploaded Dataset",
        task_type=session_state["signals"].task_type,
        model_results=session_state["results"],
        features=session_state["engineered_features"] or [],
    )
    session_state["report_markdown"] = report_data.get("markdown")
    session_state.save()
    return {"status": "success", "markdown": session_state["report_markdown"]}

@app.get("/api/report/export/{fmt}")
def export_report(fmt: str):
    """Export the current report as PDF or DOCX."""
    if fmt not in {"pdf", "docx"}:
        return {"error": "Unsupported export format. Use pdf or docx."}
    if session_state["report_markdown"] is None:
        generated = generate_report()
        if isinstance(generated, dict) and generated.get("error"):
            return generated

    from core.report_generator import ReportGenerator

    filename = f"AWIP_Report.{fmt}"
    output_path = os.path.join(os.getcwd(), filename)
    if fmt == "pdf":
        ReportGenerator.to_pdf(session_state["report_markdown"], output_path)
        media_type = "application/pdf"
    else:
        ReportGenerator.to_docx(session_state["report_markdown"], output_path)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(output_path, filename=filename, media_type=media_type)
