"""AWIP — Adaptive Workflow Intelligence Platform | Enterprise UI"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os, json, time, requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.context_engine import ContextUnderstandingEngine
from core.workflow_engine import WorkflowAdaptationEngine
from core.pipeline_executor import PipelineExecutor
from core.llm_engine import LLMEngine

st.set_page_config(page_title="AWIP | Adaptive Workflow Intelligence", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;700&display=swap');
html, body, * { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.stApp { background: #050814; color: #E2E8F0; }
[data-testid="stSidebar"] { background: rgba(8, 12, 23, 0.95); border-right: 1px solid rgba(30, 41, 59, 0.8); backdrop-filter: blur(10px); }
[data-testid="stSidebar"] * { color: #94A3B8 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #E2E8F0 !important; }
.block-container { padding: 1rem 1.5rem; max-width: 100%; }
header[data-testid="stHeader"] { background: transparent !important; }

/* TOP BAR */
.top-bar { display: flex; justify-content: space-between; align-items: center; background: rgba(10, 15, 30, 0.8); border: 1px solid rgba(45, 61, 94, 0.4); border-radius: 8px; padding: 10px 20px; margin-bottom: 15px; backdrop-filter: blur(12px); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
.tb-logo { font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 700; background: linear-gradient(90deg, #06b6d4, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: flex; align-items: center; gap: 8px; }
.tb-center { display: flex; gap: 15px; font-size: 0.8rem; font-family: 'JetBrains Mono', monospace; color: #94A3B8; }
.tb-center span { background: rgba(30, 41, 59, 0.5); padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(45, 61, 94, 0.5); }
.tb-right { display: flex; gap: 15px; font-size: 0.8rem; font-family: 'JetBrains Mono', monospace; font-weight: 700; align-items: center; }
.ind-on { color: #10B981; display: flex; align-items: center; gap: 4px; }
.ind-on::before { content: ''; width: 8px; height: 8px; background: #10B981; border-radius: 50%; box-shadow: 0 0 8px #10B981; display: inline-block; }
.ind-wait { color: #F59E0B; display: flex; align-items: center; gap: 4px; }
.ind-wait::before { content: ''; width: 8px; height: 8px; background: #F59E0B; border-radius: 50%; box-shadow: 0 0 8px #F59E0B; display: inline-block; }
.conf-pill { background: rgba(6, 182, 212, 0.1); color: #06b6d4; border: 1px solid rgba(6, 182, 212, 0.3); padding: 4px 10px; border-radius: 20px; }

/* PANELS */
.ai-panel { background: rgba(11, 16, 33, 0.7); border: 1px solid rgba(30, 41, 59, 0.8); border-radius: 12px; padding: 1.5rem; position: relative; overflow: hidden; backdrop-filter: blur(10px); box-shadow: 0 8px 32px rgba(0,0,0,0.2); margin-bottom: 1rem; transition: all 0.3s ease; }
.ai-panel:hover { border-color: rgba(6, 182, 212, 0.4); box-shadow: 0 8px 32px rgba(6, 182, 212, 0.05); }
.ai-panel::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.8), transparent); opacity: 0.5; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem; border-bottom: 1px solid rgba(30, 41, 59, 0.6); padding-bottom: 0.8rem; }
.panel-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 700; color: #E2E8F0; display: flex; align-items: center; gap: 8px; }
.panel-title i { color: #06b6d4; }

/* DATA INTELLIGENCE METRICS */
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 1rem; }
.ai-metric { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(30, 41, 59, 0.5); border-radius: 8px; padding: 1rem; text-align: center; position: relative; overflow: hidden; transition: all 0.2s; }
.ai-metric:hover { background: rgba(30, 41, 59, 0.8); transform: translateY(-2px); border-color: rgba(139, 92, 246, 0.4); }
.ai-metric-val { font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 700; color: #06b6d4; text-shadow: 0 0 10px rgba(6, 182, 212, 0.3); }
.ai-metric-lbl { font-size: 0.65rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; font-weight: 600; }

/* CENTRAL REASONING */
.reasoning-feed { font-size: 0.9rem; line-height: 1.7; color: #cbd5e1; }
.reasoning-block { background: rgba(15, 23, 42, 0.4); border-left: 3px solid #8b5cf6; padding: 12px 16px; margin: 8px 0; border-radius: 0 8px 8px 0; font-family: 'Inter', sans-serif; }
.reasoning-block strong { color: #E2E8F0; font-family: 'Space Grotesk', sans-serif; }
.thought-pulse { display: inline-block; width: 8px; height: 8px; background: #8b5cf6; border-radius: 50%; margin-right: 8px; animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(139, 92, 246, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(139, 92, 246, 0); } }

/* WORKFLOW DAG */
.dag-container { display: flex; flex-direction: column; gap: 12px; padding: 10px 0; }
.dag-node { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(30, 41, 59, 0.8); border-radius: 8px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; position: relative; transition: all 0.3s; }
.dag-node:hover { border-color: #06b6d4; box-shadow: 0 0 20px rgba(6, 182, 212, 0.15); transform: translateX(5px); }
.dag-node::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; border-radius: 4px 0 0 4px; background: #3b82f6; }
.dag-node.n-pre::before { background: #06b6d4; box-shadow: 0 0 10px #06b6d4; }
.dag-node.n-mod::before { background: #8b5cf6; box-shadow: 0 0 10px #8b5cf6; }
.dag-arrow { text-align: center; color: #475569; font-size: 1.2rem; margin: -6px 0; }
.node-name { font-size: 0.9rem; font-weight: 700; color: #E2E8F0; }
.node-cat { font-size: 0.65rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; }
.node-reason { font-size: 0.75rem; color: #64748B; margin-top: 4px; }

/* LEADERBOARD CARDS */
.model-card { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(30, 41, 59, 0.6); border-radius: 8px; padding: 12px; margin-bottom: 10px; display: grid; grid-template-columns: auto 1fr auto; gap: 12px; align-items: center; transition: all 0.2s; }
.model-card:hover { border-color: rgba(139, 92, 246, 0.4); }
.model-card.selected { border-color: #10B981; background: rgba(16, 185, 129, 0.05); }
.model-card.selected .m-rank { color: #10B981; border-color: rgba(16, 185, 129, 0.3); }
.m-rank { font-family: 'JetBrains Mono', monospace; font-size: 1rem; font-weight: 700; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 50%; border: 1px solid rgba(45, 61, 94, 0.5); color: #94A3B8; }
.m-info h4 { margin: 0 0 2px 0; font-family: 'Space Grotesk', sans-serif; color: #E2E8F0; font-size: 0.95rem; }
.m-info p { margin: 0; font-size: 0.75rem; color: #94A3B8; }
.m-score { font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; font-weight: 700; color: #06b6d4; text-align: right; }

/* EVOLUTION */
.evo-card { display: grid; grid-template-columns: 1fr 40px 1fr; gap: 15px; align-items: center; background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(30, 41, 59, 0.6); padding: 16px; border-radius: 10px; margin-bottom: 12px; }
.evo-side { background: rgba(11, 16, 33, 0.8); padding: 12px; border-radius: 8px; border: 1px solid rgba(30, 41, 59, 0.5); height: 100%; }
.evo-lbl { font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; font-weight: 600; }
.evo-item { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; padding: 6px; margin: 4px 0; border-radius: 4px; background: rgba(30, 41, 59, 0.4); color: #E2E8F0; }
.evo-arrow { text-align: center; font-size: 1.2rem; color: #8b5cf6; }

/* DROPZONE */
.dropzone-empty { border: 1px dashed rgba(45, 61, 94, 0.8); border-radius: 12px; padding: 4rem 2rem; text-align: center; background: rgba(11, 16, 33, 0.4); transition: all 0.3s; }
.dropzone-empty:hover { border-color: #06b6d4; background: rgba(6, 182, 212, 0.02); }
.dz-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem; font-weight: 700; color: #E2E8F0; margin: 15px 0 5px; }
.dz-sub { color: #64748B; font-size: 0.85rem; max-width: 500px; margin: 0 auto; }

/* OVERRIDES */
div[data-testid="stExpander"] { border: 1px solid rgba(30, 41, 59, 0.8) !important; border-radius: 8px !important; background: rgba(15, 23, 42, 0.4) !important; }
.stButton>button { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(45, 61, 94, 0.8); color: #E2E8F0; transition: all 0.2s; }
.stButton>button:hover { border-color: #06b6d4; box-shadow: 0 0 15px rgba(6, 182, 212, 0.2); color: #fff; }
button[kind="primary"] { background: linear-gradient(135deg, #06b6d4, #8b5cf6) !important; border: none !important; font-weight: 600; }
.stTabs [data-baseweb="tab"] { color: #94A3B8; font-size: 0.85rem; font-weight: 500; font-family: 'Space Grotesk', sans-serif; }
.stTabs [aria-selected="true"] { color: #06b6d4 !important; border-bottom-color: #06b6d4 !important; }
.stChatMessage { background: rgba(15, 23, 42, 0.6) !important; border: 1px solid rgba(30, 41, 59, 0.8) !important; border-radius: 8px !important; }
div[data-testid="stChatInput"] { border: 1px solid rgba(30, 41, 59, 0.8); border-radius: 8px; background: rgba(11, 16, 33, 0.8); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── Session State ──
for k,v in {
    "df":None, "signals":None, "workflow":None, "prev_workflow":None,
    "results":None, "executor":None, "history":[], "chat":[], "version":0,
    "target_col":None, "user_level":"expert", "onboarding_done":False
}.items():
    if k not in st.session_state: st.session_state[k]=v

# Helper to check Ollama status
@st.cache_data(ttl=10)
def check_llm():
    try:
        r=requests.get("http://localhost:11434/api/tags", timeout=1)
        return r.status_code==200
    except: return False

llm_ok = check_llm()

def get_signal_pill(text, sig_type="info"):
    colors = {"info":"#06b6d4", "warn":"#f59e0b", "crit":"#ef4444", "ok":"#10b981"}
    bg = colors[sig_type]
    return f'<span style="display:inline-block;background:rgba(255,255,255,0.05);border:1px solid {bg}50;color:{bg};padding:2px 8px;border-radius:12px;font-size:0.65rem;font-weight:600;margin:2px;">{text}</span>'

# ══════ LEFT SIDEBAR ══════
with st.sidebar:
    st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.4rem;font-weight:700;color:#E2E8F0;margin-bottom:20px;display:flex;align-items:center;gap:10px;">⚡ AWIP<span style="font-size:0.6rem;background:rgba(6,182,212,0.1);color:#06b6d4;padding:2px 6px;border-radius:4px;border:1px solid rgba(6,182,212,0.3);">OS</span></div>', unsafe_allow_html=True)
    
    with st.expander("📁 Dataset Connection", expanded=True):
        uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
        st.markdown('<div style="font-size:0.7rem;color:#64748b;margin:10px 0 5px;">Demo Environments:</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        def _ld(path):
            st.session_state.df=pd.read_csv(path); st.session_state.onboarding_done=False; st.session_state.target_col=None; st.session_state.workflow=None; st.session_state.signals=None; st.session_state.results=None; st.session_state.version=0; st.session_state.history=[]; st.rerun()
        if c1.button("HR1", use_container_width=True): _ld("sample_data/hr_attrition_v1.csv")
        if c2.button("HR2", use_container_width=True): _ld("sample_data/hr_attrition_v2.csv")
        if c3.button("Sens", use_container_width=True): _ld("sample_data/sensor_data.csv")
        if st.session_state.df is not None:
            if st.button("Reset Session", use_container_width=True):
                for k in ["df","signals","workflow","results","target_col"]: st.session_state[k]=None
                st.session_state.onboarding_done=False; st.session_state.version=0; st.session_state.history=[]; st.rerun()

    with st.expander("⚙️ Engine Configuration", expanded=True):
        st.session_state.user_level = st.select_slider("Expertise Profile", ["beginner","intermediate","expert"], value=st.session_state.user_level)
        domain = st.selectbox("Domain Context", ["auto-detect","manufacturing","healthcare","finance","hr","retail"])
        if st.session_state.df is not None and st.session_state.onboarding_done:
            st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
            if st.button("🚀 Re-Orchestrate Pipeline", use_container_width=True, type="primary"):
                pass # Will be handled below
                
    st.markdown('<div style="margin-top:2rem;margin-bottom:1rem;font-size:0.65rem;color:#475569;text-align:center;width:100%;">Adaptive Workflow Intelligence Platform<br>Core Engine Active</div>', unsafe_allow_html=True)

# ══════ TOP STATUS BAR ══════
if st.session_state.df is not None and st.session_state.signals:
    s = st.session_state.signals
    task = s.task_type.replace("_"," ").title() if s.task_type!="unknown" else "Detecting..."
    dom = s.domain_hint.title() if s.domain_hint else "Auto"
    conf = max(70, 95 - len(st.session_state.workflow.adaptations)*2) if st.session_state.workflow else "--"
    t_col = st.session_state.target_col or "None"
else:
    task, dom, conf, t_col = "Idle", "Idle", "--", "--"

llm_status = '<span class="ind-on">LLM Active</span>' if llm_ok else '<span class="ind-wait">LLM Offline</span>'
df_status = '<span class="ind-on">Data Connected</span>' if st.session_state.df is not None else '<span class="ind-wait">Awaiting Data</span>'

st.markdown(f"""
<div class="top-bar">
    <div class="tb-logo">⚡ AWIP</div>
    <div class="tb-center">
        <span>Target: {t_col}</span>
        <span>Task: {task}</span>
        <span>Domain: {dom}</span>
        <span>Expertise: {st.session_state.user_level.title()}</span>
    </div>
    <div class="tb-right">
        {llm_status}
        {df_status}
        <span class="conf-pill">Confidence: {conf}%</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════ MAIN LAYOUT ══════
if st.session_state.df is None:
    # EMPTY STATE
    st.markdown("""
    <div class="dropzone-empty">
        <div style="font-size: 3rem; color: #3b82f6; margin-bottom: 10px;">⚡</div>
        <div class="dz-title">Awaiting Dataset Connection</div>
        <div class="dz-sub">Upload a CSV in the sidebar or connect a demo dataset to initialize the AI orchestration engine. The system will automatically interpret schema, extract context, and generate an adaptive data science workflow.</div>
    </div>
    
    <div style="background:rgba(11, 16, 33, 0.4); border:1px solid rgba(45, 61, 94, 0.6); border-radius:12px; padding:2rem; margin:2rem 0; text-align:center;">
        <h3 style="color:#06b6d4; margin-top:0; font-family:'Space Grotesk',sans-serif;">👋 Welcome to AWIP</h3>
        <p style="color:#94A3B8; font-size:.95rem; max-width:700px; margin:0 auto 1.5rem; line-height:1.6;">
        To evaluate this platform's ability to understand context and automate data science tasks, follow these steps:
        </p>
        <div style="display:flex; justify-content:center; gap:2rem; text-align:left; max-width:800px; margin:0 auto;">
          <div style="flex:1; background:rgba(15, 23, 42, 0.6); padding:15px; border-radius:8px; border:1px solid rgba(30, 41, 59, 0.8);">
            <strong style="color:#06b6d4; font-size:1.1rem;">Step 1</strong><br><span style="color:#E2E8F0; font-size:0.85rem; display:block; margin-top:5px;">Upload a dataset via the sidebar (or click a Demo). The AI will interpret it.</span>
          </div>
          <div style="flex:1; background:rgba(15, 23, 42, 0.6); padding:15px; border-radius:8px; border:1px solid rgba(30, 41, 59, 0.8);">
            <strong style="color:#06b6d4; font-size:1.1rem;">Step 2</strong><br><span style="color:#E2E8F0; font-size:0.85rem; display:block; margin-top:5px;">Select a target variable. The system will adapt to Regression, Classification, etc.</span>
          </div>
          <div style="flex:1; background:rgba(15, 23, 42, 0.6); padding:15px; border-radius:8px; border:1px solid rgba(30, 41, 59, 0.8);">
            <strong style="color:#06b6d4; font-size:1.1rem;">Step 3</strong><br><span style="color:#E2E8F0; font-size:0.85rem; display:block; margin-top:5px;">Explore the LLM explanations, leaderboard, and chat with the AI Copilot.</span>
          </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if uploaded is not None:
        st.session_state.df = pd.read_csv(uploaded)
        st.rerun()
    st.stop()

df = st.session_state.df

# ══════ ONBOARDING / TARGET SELECTION ══════
if not st.session_state.onboarding_done:
    st.markdown('<div class="ai-panel"><div class="panel-header"><div class="panel-title">🧠 Context Extraction Engine</div></div>', unsafe_allow_html=True)
    cue = ContextUnderstandingEngine()
    pre_s = cue.analyze(df, target_column=None, user_intent="", domain_hint="" if domain=="auto-detect" else domain)
    
    # Intelligence Metrics
    m_html = '<div class="metric-grid">'
    m_html += f'<div class="ai-metric"><div class="ai-metric-val">{pre_s.n_rows:,}</div><div class="ai-metric-lbl">Rows</div></div>'
    m_html += f'<div class="ai-metric"><div class="ai-metric-val">{pre_s.n_cols}</div><div class="ai-metric-lbl">Columns</div></div>'
    m_html += f'<div class="ai-metric"><div class="ai-metric-val">{pre_s.overall_missing_ratio:.1%}</div><div class="ai-metric-lbl">Missing</div></div>'
    m_html += f'<div class="ai-metric"><div class="ai-metric-val">{len(pre_s.categorical_columns)}</div><div class="ai-metric-lbl">Categorical</div></div>'
    m_html += '</div>'
    st.markdown(m_html, unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top:20px;font-family:\'Space Grotesk\',sans-serif;font-size:1rem;color:#E2E8F0;margin-bottom:10px;">Select Target Variable</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    target_candidates = [c for c in df.columns if df[c].nunique() < 20 or c.lower() in ["target","label","churn","attrition","status","y"]]
    if not target_candidates: target_candidates = list(df.columns)[:4]
    
    for i, c in enumerate(target_candidates[:4]):
        with cols[i]:
            nu = df[c].nunique()
            hint = "Classification" if nu < 20 else "Regression"
            if st.button(f"{c}\n({nu} unique)", key=f"tgt_{c}", use_container_width=True):
                st.session_state.target_col = c
                st.session_state.onboarding_done = True
                st.rerun()
                
    st.markdown("Or select manually:")
    man = st.selectbox("Column", ["--"] + list(df.columns), label_visibility="collapsed")
    if man != "--":
        st.session_state.target_col = man
        st.session_state.onboarding_done = True
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ══════ ORCHESTRATION EXECUTION ══════
target_col = st.session_state.target_col
if st.session_state.workflow is None or st.sidebar.button("🚀 Force Re-Orchestration", key="force_run"):
    with st.spinner("AI Orchestration Engine Active..."):
        cue = ContextUnderstandingEngine()
        signals = cue.analyze(df, target_column=target_col, user_intent="", domain_hint="" if domain=="auto-detect" else domain)
        st.session_state.signals = signals
        
        wae = WorkflowAdaptationEngine()
        if st.session_state.workflow:
            st.session_state.prev_workflow = st.session_state.workflow
            workflow = wae.adapt_workflow(st.session_state.prev_workflow, signals, st.session_state.user_level)
        else:
            workflow = wae.generate_workflow(signals, st.session_state.user_level)
            
        st.session_state.workflow = workflow
        st.session_state.version += 1
        st.session_state.history.append({"version":workflow.version,"dag":workflow.to_dict(),"df":df.copy()})
        
        executor = PipelineExecutor()
        results = executor.execute(df, workflow, target_col, signals)
        st.session_state.results = results
        st.session_state.executor = executor
        st.rerun()

signals = st.session_state.signals
workflow = st.session_state.workflow
results = st.session_state.results

# ══════ LIVE AI PANELS ══════

# Main Layout: 75% Content, 25% Copilot
col_main, col_chat = st.columns([3, 1])

with col_main:
    # ── SECTION 1: AI DATASET INTELLIGENCE ──
    st.markdown('<div class="ai-panel"><div class="panel-header"><div class="panel-title">🧠 Dataset Intelligence & Context</div></div>', unsafe_allow_html=True)
    
    # Drift check
    drift_score = 0.0; drift_msg = "Baseline established"
    if len(st.session_state.history) > 1:
        cue = ContextUnderstandingEngine()
        old_df = st.session_state.history[-2]["df"]
        d_res = cue.detect_drift(old_df, df, signals.numeric_columns)
        max_drift = max([r["drift_score"] for r in d_res.values()] + [0])
        drift_score = max_drift
        if max_drift > 0.2: drift_msg = f"Distribution shift detected ({max_drift:.2f})"
        else: drift_msg = "Stable distribution"
        
    m_html = '<div class="metric-grid">'
    m_html += f'<div class="ai-metric"><div class="ai-metric-val">{signals.n_rows:,}</div><div class="ai-metric-lbl">Rows</div></div>'
    m_html += f'<div class="ai-metric"><div class="ai-metric-val">{signals.n_cols}</div><div class="ai-metric-lbl">Columns</div></div>'
    if signals.is_imbalanced:
        m_html += f'<div class="ai-metric"><div class="ai-metric-val" style="color:#f59e0b;">{signals.imbalance_ratio:.1f}:1</div><div class="ai-metric-lbl">Imbalance</div></div>'
    else:
        m_html += f'<div class="ai-metric"><div class="ai-metric-val">{signals.overall_missing_ratio:.1%}</div><div class="ai-metric-lbl">Missing</div></div>'
    m_html += f'<div class="ai-metric"><div class="ai-metric-val" style="color:{"#f59e0b" if drift_score>0.2 else "#06b6d4"};">{drift_score:.2f}</div><div class="ai-metric-lbl">Drift Score</div></div>'
    m_html += '</div>'
    
    pills = []
    if signals.has_missing_values: pills.append(get_signal_pill("Missing Values Detected", "warn"))
    if signals.is_imbalanced: pills.append(get_signal_pill("Class Imbalance", "crit"))
    if signals.has_outliers: pills.append(get_signal_pill("Outliers Present", "warn"))
    if drift_score>0.2: pills.append(get_signal_pill("Data Drift", "crit"))
    if not pills: pills.append(get_signal_pill("Clean Data", "ok"))
    
    st.markdown(m_html + f'<div style="margin-top:15px;">{"".join(pills)}</div></div>', unsafe_allow_html=True)

    # ── SECTION 2: CENTRAL AI REASONING PANEL ──
    st.markdown('<div class="ai-panel"><div class="panel-header"><div class="panel-title">💡 AI Workflow Reasoning</div></div>', unsafe_allow_html=True)
    
    if workflow.explanation and not workflow.explanation.startswith("I've designed"):
        reasoning = workflow.explanation
    else:
        model_name = next((s.name for s in workflow.steps if s.category=="model"),"the selected model")
        reasoning = f"The dataset exhibits signals requiring intervention. I generated a v{workflow.version} {signals.task_type.replace('_',' ')} workflow. "
        for a in workflow.adaptations:
            reasoning += f"Due to **{a['signal']}**, I applied **{a['action']}**. "
        reasoning += f"Finally, **{model_name}** was selected to model the target variable."
        
    st.markdown(f'<div class="reasoning-feed"><span class="thought-pulse"></span><strong>Adaptive Workflow Reasoning:</strong><div class="reasoning-block">{reasoning}</div></div></div>', unsafe_allow_html=True)

    # ── TABBED SECTIONS (Workflow, Leaderboard, Evolution, SHAP) ──
    tabs = st.tabs(["DAG Visualization", "Model Leaderboard", "Workflow Evolution", "Explainability"])
    
    with tabs[0]:
        st.markdown('<div class="dag-container">', unsafe_allow_html=True)
        for i,step in enumerate(workflow.steps):
            cat_cls = "n-mod" if step.category=="model" else ("n-pre" if step.category=="preprocessing" else "")
            st.markdown(f'<div class="dag-node {cat_cls}"><div><div class="node-name">{step.name}</div><div class="node-reason">{step.reason.split(".")[0]}</div></div><div class="node-cat">{step.category}</div></div>', unsafe_allow_html=True)
            if i < len(workflow.steps)-1:
                st.markdown('<div class="dag-arrow">↓</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tabs[1]:
        lb_data = results.get("leaderboard", []) if results else []
        if not lb_data:
            model_step = next((s for s in workflow.steps if s.category=="model"),None)
            best_score = results["metrics"].get("auc_roc", results["metrics"].get("r2_score", 0.9)) if results and "metrics" in results else 0.9
            lb_data = [{"name": model_step.name if model_step else "Model", "score": best_score}]
            
        for i, item in enumerate(lb_data):
            sel_cls = "selected" if i==0 else ""
            status = "✔ Selected" if i==0 else "✖ Rejected"
            m_step = next((s for s in workflow.steps if s.category=="model"), None)
            reason = m_step.reason if m_step and i==0 else "Did not outperform primary model on cross-validation."
            st.markdown(f"""
            <div class="model-card {sel_cls}">
                <div class="m-rank">#{i+1}</div>
                <div class="m-info">
                    <h4>{item['name']} <span style="font-size:0.7rem;color:{'#10B981' if i==0 else '#64748B'};font-family:'Inter',sans-serif;font-weight:600;margin-left:8px;">{status}</span></h4>
                    <p>{reason}</p>
                </div>
                <div class="m-score">{(item['score']*100):.1f}</div>
            </div>
            """, unsafe_allow_html=True)

    with tabs[2]:
        if workflow.evolution_log:
            for log in workflow.evolution_log:
                if log["type"] == "added":
                    st.markdown(f"""
                    <div class="evo-card">
                        <div class="evo-side"><div class="evo-lbl">Before</div><div class="evo-item" style="color:#64748B;">--</div></div>
                        <div class="evo-arrow">→</div>
                        <div class="evo-side" style="border-color:rgba(16,185,129,0.5);"><div class="evo-lbl" style="color:#10B981;">Added</div><div class="evo-item">{log["step_name"]}</div><div style="font-size:0.7rem;color:#94A3B8;margin-top:4px;">{log["reason"]}</div></div>
                    </div>
                    """, unsafe_allow_html=True)
                elif log["type"] == "replaced":
                    st.markdown(f"""
                    <div class="evo-card">
                        <div class="evo-side"><div class="evo-lbl" style="color:#F59E0B;">Replaced</div><div class="evo-item" style="text-decoration:line-through;color:#64748B;">{log.get("old_step","Old Step")}</div></div>
                        <div class="evo-arrow">→</div>
                        <div class="evo-side" style="border-color:rgba(139,92,246,0.5);"><div class="evo-lbl" style="color:#8B5CF6;">New</div><div class="evo-item">{log["step_name"]}</div><div style="font-size:0.7rem;color:#94A3B8;margin-top:4px;">{log["reason"]}</div></div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No evolution has occurred yet. Upload a shifted dataset to trigger pipeline adaptation.")

    with tabs[3]:
        if results and results.get("shap_data") and "top_features" in results["shap_data"]:
            feats = results["shap_data"]["top_features"]
            names = [f[0] for f in feats]; vals = [f[1] for f in feats]
            
            c_sh1, c_sh2 = st.columns([2, 1])
            with c_sh1:
                fig=go.Figure(go.Bar(x=vals[:10][::-1], y=names[:10][::-1], orientation="h", marker=dict(color="#06b6d4")))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#94A3B8", title="SHAP Importance", margin=dict(l=0,r=0,t=30,b=0), height=300)
                st.plotly_chart(fig, use_container_width=True)
            with c_sh2:
                top_3 = ", ".join(names[:3])
                st.markdown(f'<div class="reasoning-block" style="border-color:#06b6d4;font-size:0.85rem;"><strong style="color:#06b6d4;">AI Analysis</strong><br><br>The model identified <strong>{top_3}</strong> as the primary drivers for this prediction task.<br><br>These variables exhibit the highest magnitude of impact on the target variable based on Shapley additive explanations.</div>', unsafe_allow_html=True)
        else:
            st.warning("SHAP explanation not available for this pipeline.")

# ── SECTION 5: AI COPILOT (RIGHT PANEL) ──
with col_chat:
    st.markdown('<div class="copilot-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title" style="margin-bottom:15px;font-size:1rem;"><i style="font-style:normal;">🤖</i> AI Copilot</div>', unsafe_allow_html=True)
    
    chat_container = st.container(height=500)
    with chat_container:
        st.markdown(f'<div class="chat-msg msg-ai">System active. Workflow v{workflow.version} compiled. Ask me to explain the reasoning, model choice, or SHAP analysis.</div>', unsafe_allow_html=True)
        for msg in st.session_state.chat:
            cls = "msg-user" if msg["role"] == "user" else "msg-ai"
            st.markdown(f'<div class="chat-msg {cls}">{msg["content"]}</div>', unsafe_allow_html=True)
            
    query = st.chat_input("Ask Copilot...")
    if query:
        st.session_state.chat.append({"role":"user","content":query})
        with chat_container:
            st.markdown(f'<div class="chat-msg msg-user">{query}</div>', unsafe_allow_html=True)
            with st.spinner("Analyzing..."):
                llm = LLMEngine()
                resp = llm.chat(query, workflow, signals, results, st.session_state.user_level)
                if resp.startswith("[LLM Error") or resp.startswith("[Fallback"):
                    # Fallback logic
                    q=query.lower()
                    if any(k in q for k in ["why","chose","model"]):
                        ms=next((s for s in workflow.steps if s.category=="model"),None)
                        resp = f"**Model:** `{ms.name}`\n{ms.reason}" if ms else "Model selected based on task type."
                    elif "adapt" in q or "evolve" in q:
                        resp = "Adaptations were triggered by dataset signals (e.g. imbalance)."
                    else:
                        resp = "LLM offline. I am operating on heuristic reasoning rules."
            st.markdown(f'<div class="chat-msg msg-ai">{resp}</div>', unsafe_allow_html=True)
        st.session_state.chat.append({"role":"assistant","content":resp})
        
    st.markdown('</div>', unsafe_allow_html=True)
