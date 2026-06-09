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
from datetime import datetime

# Add backend directory to sys.path so core modules can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agents.orchestrator import OrchestratorAgent
from core.knowledge_memory import KnowledgeBase
from core.intent_parser import IntentParser

app = FastAPI(title="AWIP AI Data Science Workspace API", version="3.0.0")

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

# In-memory session state for demo purposes (ideally this goes to DB/Redis)
session_state = {
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
}

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
        None,
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

    knowledge_base.add_experiment(
        dataset_name=session_state["dataset_name"] or "Uploaded Dataset",
        task_type=signals.task_type,
        domain=getattr(signals, "domain_hint", "auto-detect"),
        winner_model=winner_model,
        score=score,
        features_added=len(features),
        key_issues=getattr(signals, "quality_issues", []) or [],
    )

    workflow_dict = workflow.to_dict() if workflow else None

    return _json_safe({
        "status": "success",
        "workflow": workflow_dict,
        "results": metrics,
        "leaderboard": results.get("leaderboard", []) if results else [],
        "report": session_state["report_markdown"],
        "messages": [_message_to_dict(m) for m in session_state["agent_messages"]],
    })

@app.get("/")
def read_root():
    return {"status": "AWIP Backend Running"}

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Uploads a dataset and initializes the workspace."""
    content = await file.read()
    # Save temporarily to parse into pandas
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(content)
        
    try:
        df = pd.read_csv(temp_path)
        if session_state["df"] is not None:
            session_state["previous_df"] = session_state["df"].copy()
        session_state["df"] = df
        session_state["dataset_name"] = file.filename
        
        # We can trigger initial context extraction here
        from core.context_engine import ContextUnderstandingEngine
        cue = ContextUnderstandingEngine()
        signals = cue.analyze(df, target_column=None, user_intent="", domain_hint="auto-detect")
        session_state["signals"] = signals
        
        dataset_record = {
            "name": file.filename,
            "rows": int(signals.n_rows),
            "cols": int(signals.n_cols),
            "task_type": signals.task_type,
            "uploaded_at": datetime.now().isoformat(),
        }
        session_state["datasets"].append(dataset_record)

        return {
            "status": "success", 
            "dataset": file.filename, 
            "rows": signals.n_rows,
            "cols": signals.n_cols,
            "task_type": signals.task_type
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
    return {"datasets": session_state["datasets"], "active": session_state["dataset_name"]}

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

@app.get("/api/feed")
def get_agent_feed():
    """Returns the live agent activity feed."""
    msgs = session_state["agent_messages"]
    return {"messages": [_message_to_dict(m) for m in msgs]}

@app.post("/api/chat")
def chat_command(req: CommandRequest):
    """Processes natural language commands."""
    intent_res = intent_parser.parse_intent(req.command)
    
    # Normally we'd process the intent and run LLM
    from core.llm_engine import LLMEngine
    llm = LLMEngine()
    resp = llm.chat_with_context(
        req.command, 
        session_state["workflow"], 
        session_state["signals"], 
        session_state["results"],
        knowledge_base=knowledge_base,
        agent_messages=session_state["agent_messages"]
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
        features=session_state["engineered_features"],
    )
    session_state["report_markdown"] = report_data.get("markdown")
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
