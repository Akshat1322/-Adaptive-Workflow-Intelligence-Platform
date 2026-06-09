"""AWIP — Adaptive Workflow Intelligence Platform | Phase 3: AI Data Science Workspace"""

import streamlit as st
import pandas as pd
import sys, os, time
import plotly.express as px

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.context_engine import ContextUnderstandingEngine
from core.llm_engine import LLMEngine
from core.knowledge_memory import KnowledgeBase
from core.agents.orchestrator import OrchestratorAgent
from core.intent_parser import IntentParser
from core.visuals import generate_interactive_dag, generate_experiment_comparison
from core.report_generator import ReportGenerator

st.set_page_config(page_title="AWIP | AI Workspace", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;700&display=swap');
html, body, * { font-family: 'Inter', sans-serif; box-sizing: border-box; }
.stApp { background: #050814; color: #E2E8F0; }
.block-container { padding: 1rem 1.5rem; max-width: 100%; }
header[data-testid="stHeader"], [data-testid="stSidebar"] { display: none !important; }

/* Panels */
.nav-panel { background: rgba(11, 16, 33, 0.7); border-right: 1px solid rgba(30, 41, 59, 0.8); height: 95vh; padding: 1rem; border-radius: 12px; }
.center-panel { padding: 0 1rem; }
.ai-panel { background: rgba(11, 16, 33, 0.7); border-left: 1px solid rgba(30, 41, 59, 0.8); height: 95vh; padding: 1rem; border-radius: 12px; }

/* Glassmorphism Cards */
.glass-card { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(30, 41, 59, 0.5); border-radius: 12px; padding: 1rem; backdrop-filter: blur(10px); margin-bottom: 1rem; }

/* Command Palette */
.cmd-palette input { background: rgba(15, 23, 42, 0.8) !important; border: 1px solid rgba(139, 92, 246, 0.5) !important; color: #E2E8F0 !important; font-family: 'JetBrains Mono', monospace !important; border-radius: 8px !important; }

/* Agent Chat */
.chat-msg { margin-bottom: 12px; padding: 12px; border-radius: 8px; font-size: 0.85rem; line-height: 1.5; }
.msg-ai { background: rgba(15, 23, 42, 0.6); border-left: 3px solid #06b6d4; color: #cbd5e1; }
.msg-user { background: rgba(139, 92, 246, 0.1); border-right: 3px solid #8b5cf6; text-align: right; color: #E2E8F0; }

.nav-btn { display: block; width: 100%; padding: 10px; margin-bottom: 8px; text-align: left; background: transparent; border: 1px solid transparent; color: #94A3B8; border-radius: 6px; cursor: pointer; transition: all 0.2s; font-weight: 500; }
.nav-btn:hover { background: rgba(30, 41, 59, 0.5); color: #E2E8F0; }
.nav-btn.active { background: rgba(139, 92, 246, 0.15); border-color: rgba(139, 92, 246, 0.3); color: #8b5cf6; font-weight: 600; }

.ai-metric { text-align: center; }
.ai-metric-val { font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 700; color: #06b6d4; }
.ai-metric-lbl { font-size: 0.65rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── Session State ──
for k,v in {
    "df":None, "signals":None, "workflow":None, "results":None, 
    "history":[], "chat":[], "target_col":None, "user_level":"expert", 
    "engineered_features":[], "agent_messages":[], "dataset_name":"Uploaded Dataset",
    "current_page": "home", "onboarding_done": False
}.items():
    if k not in st.session_state: st.session_state[k]=v

if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = KnowledgeBase()
if "intent_parser" not in st.session_state:
    st.session_state.intent_parser = IntentParser()

# ── LAYOUT ──
col_nav, col_center, col_right = st.columns([1.5, 6, 2.5], gap="small")

def set_page(page):
    st.session_state.current_page = page

# ══════ LEFT PANEL: NAVIGATION ══════
with col_nav:
    st.markdown('<div class="nav-panel">', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.2rem;font-weight:700;color:#E2E8F0;margin-bottom:20px;">⚡ AWIP Workspace</div>', unsafe_allow_html=True)
    
    pages = {"home": "🏠 Intelligence Home", "experiments": "🔬 Experiment Lab", "knowledge": "📚 Knowledge Base", "reports": "📄 Report Studio"}
    for k, label in pages.items():
        if st.button(label, use_container_width=True, type="primary" if st.session_state.current_page == k else "secondary"):
            set_page(k)
            st.rerun()

    st.markdown("<hr style='border-color: rgba(30,41,59,0.8); margin: 20px 0;'>", unsafe_allow_html=True)
    
    # Dataset Connection
    st.markdown("<div style='font-size:0.8rem;color:#94A3B8;margin-bottom:8px;'>DATASET</div>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
    if uploaded:
        st.session_state.df = pd.read_csv(uploaded)
        st.session_state.dataset_name = uploaded.name.replace(".csv","")
        st.session_state.onboarding_done = False
        st.session_state.current_page = "home"
        st.rerun()
        
    st.markdown("</div>", unsafe_allow_html=True)


# ══════ ORCHESTRATION EXECUTION ══════
df = st.session_state.df
if df is not None and not st.session_state.onboarding_done:
    with col_center:
        st.markdown('<div class="glass-card"><h3>🧠 Target Selection</h3>', unsafe_allow_html=True)
        cols = st.columns(4)
        target_candidates = [c for c in df.columns if df[c].nunique() < 20 or c.lower() in ["target","label","churn"]]
        if not target_candidates: target_candidates = list(df.columns)[:4]
        for i, c in enumerate(target_candidates[:4]):
            with cols[i]:
                if st.button(f"{c}", use_container_width=True):
                    st.session_state.target_col = c
                    st.session_state.onboarding_done = True
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

if df is not None and st.session_state.onboarding_done and st.session_state.workflow is None:
    with col_center:
        with st.spinner("🤖 AI Data Science Team is reasoning and experimenting..."):
            orchestrator = OrchestratorAgent()
            loop_results = orchestrator.run_iterative_loop(df, st.session_state.target_col, None, domain_hint="auto-detect")
            
            st.session_state.signals = loop_results["signals"]
            st.session_state.engineered_features = loop_results["engineered_features"]
            st.session_state.workflow = loop_results["workflow"]
            st.session_state.results = loop_results["results"]
            st.session_state.agent_messages = orchestrator.message_bus.get_all()
            st.session_state.history.append({"df": df.copy(), "workflow": loop_results["workflow"]})
            
            st.session_state.knowledge_base.add_experiment(
                dataset_name=st.session_state.dataset_name,
                task_type=st.session_state.signals.task_type,
                domain=st.session_state.signals.domain_hint,
                winner_model=next((s.name for s in loop_results["workflow"].steps if s.category == "model"), "Unknown"),
                score=loop_results["results"].get("metrics", {}).get("accuracy", 0.0),
                features_added=len(loop_results["engineered_features"]),
                key_issues=[]
            )
            st.rerun()

# ══════ CENTER PANEL: WORKSPACE ══════
with col_center:
    st.markdown('<div class="center-panel">', unsafe_allow_html=True)
    
    # Command Palette
    st.markdown('<div class="cmd-palette">', unsafe_allow_html=True)
    cmd = st.text_input("Ctrl + K (Cmd Palette)", placeholder="Type a command to AI: 'Generate report', 'Show knowledge base', 'Compare experiments'...", label_visibility="collapsed")
    if cmd:
        intent_res = st.session_state.intent_parser.parse_intent(cmd)
        intent = intent_res.get("intent")
        
        # Add to chat
        st.session_state.chat.append({"role": "user", "content": cmd})
        
        if intent == "NAVIGATE":
            if "report" in cmd.lower(): set_page("reports")
            elif "experiment" in cmd.lower(): set_page("experiments")
            elif "knowledge" in cmd.lower(): set_page("knowledge")
            else: set_page("home")
            st.session_state.chat.append({"role": "assistant", "content": f"Navigating to {st.session_state.current_page}."})
            st.rerun()
        elif intent == "GENERATE_REPORT":
            set_page("reports")
            st.session_state.chat.append({"role": "assistant", "content": "Navigating to Report Studio. You can generate a report there."})
            st.rerun()
        else:
            # Fallback to LLM chat
            with st.spinner("Thinking..."):
                llm = LLMEngine()
                resp = llm.chat_with_context(
                    cmd, st.session_state.workflow, st.session_state.signals, st.session_state.results,
                    knowledge_base=st.session_state.knowledge_base,
                    agent_messages=st.session_state.agent_messages
                )
                st.session_state.chat.append({"role": "assistant", "content": resp})

    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.df is None:
        st.markdown('<div class="glass-card" style="text-align:center; padding: 4rem;"><h2>AWIP Intelligence Workspace</h2><p style="color:#64748B;">Upload a dataset to begin.</p></div>', unsafe_allow_html=True)
    else:
        page = st.session_state.current_page
        
        if page == "home":
            st.markdown("### 📊 Dataset Intelligence Home")
            
            # Metrics
            cols = st.columns(4)
            s = st.session_state.signals
            if s:
                with cols[0]: st.markdown(f'<div class="glass-card ai-metric"><div class="ai-metric-val">{s.n_rows:,}</div><div class="ai-metric-lbl">Rows</div></div>', unsafe_allow_html=True)
                with cols[1]: st.markdown(f'<div class="glass-card ai-metric"><div class="ai-metric-val">{s.n_cols}</div><div class="ai-metric-lbl">Columns</div></div>', unsafe_allow_html=True)
                with cols[2]: st.markdown(f'<div class="glass-card ai-metric"><div class="ai-metric-val">{s.overall_missing_ratio:.1%}</div><div class="ai-metric-lbl">Missing</div></div>', unsafe_allow_html=True)
                with cols[3]: st.markdown(f'<div class="glass-card ai-metric"><div class="ai-metric-val">{s.task_type.replace("_"," ").title()}</div><div class="ai-metric-lbl">Task</div></div>', unsafe_allow_html=True)
            
            st.markdown("### 🧬 Interactive Workflow DAG")
            if st.session_state.workflow:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                fig = generate_interactive_dag(st.session_state.workflow.steps)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
        elif page == "experiments":
            st.markdown("### 🔬 Experiment Lab")
            exps = st.session_state.knowledge_base.get_experiments()
            if exps:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                fig = generate_experiment_comparison(exps)
                if fig: st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                for exp in exps:
                    st.markdown(f'<div class="glass-card"><b>{exp["dataset_name"]}</b> | Score: {exp["score"]:.4f} | Winner: {exp["winner_model"]}</div>', unsafe_allow_html=True)
            else:
                st.info("No experiments run yet.")
                
        elif page == "knowledge":
            st.markdown("### 📚 Knowledge Workspace")
            st.markdown('<div class="glass-card"><b>Query Historical Learnings</b><br><span style="color:#64748B;">Use the command palette to ask natural language questions about past experiments.</span></div>', unsafe_allow_html=True)
            
        elif page == "reports":
            st.markdown("### 📄 Report Studio")
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            if st.session_state.results and st.session_state.workflow:
                report_content = f"# Executive Summary\n\nDataset: {st.session_state.dataset_name}\n"
                report_content += f"Task: {st.session_state.signals.task_type}\n\n"
                report_content += "## Findings\n"
                report_content += "The AI Data Science team successfully generated a pipeline.\n"
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Export to PDF", use_container_width=True):
                        ReportGenerator.to_pdf(report_content, "AWIP_Report.pdf")
                        st.success("AWIP_Report.pdf generated in project root.")
                with col_btn2:
                    if st.button("Export to DOCX", use_container_width=True):
                        ReportGenerator.to_docx(report_content, "AWIP_Report.docx")
                        st.success("AWIP_Report.docx generated in project root.")
                        
                st.text_area("Report Content (Editable)", value=report_content, height=300)
            else:
                st.info("Run a workflow to generate a report.")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════ RIGHT PANEL: AI INTELLIGENCE ══════
with col_right:
    st.markdown('<div class="ai-panel">', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1rem;font-weight:700;color:#06b6d4;margin-bottom:15px;">🤖 AI Headquarters</div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["💬 Copilot", "⏱️ Activity Stream"])
    
    with tabs[0]:
        chat_container = st.container(height=500)
        with chat_container:
            for msg in st.session_state.chat:
                cls = "msg-user" if msg["role"] == "user" else "msg-ai"
                st.markdown(f'<div class="chat-msg {cls}">{msg["content"]}</div>', unsafe_allow_html=True)
                
    with tabs[1]:
        stream_container = st.container(height=500)
        with stream_container:
            if st.session_state.agent_messages:
                for msg in reversed(st.session_state.agent_messages):
                    t = msg.timestamp.split("T")[-1][:8]
                    color = "#06b6d4" if msg.sender == "Orchestrator" else "#8b5cf6"
                    st.markdown(f"""
                    <div style="border-left: 2px solid {color}; padding-left: 10px; margin-bottom: 15px;">
                        <div style="font-size: 0.7rem; color: #64748B;">{t} | {msg.sender}</div>
                        <div style="font-size: 0.8rem; color: #cbd5e1;">{msg.content}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No agent activity yet.")

    st.markdown('</div>', unsafe_allow_html=True)
