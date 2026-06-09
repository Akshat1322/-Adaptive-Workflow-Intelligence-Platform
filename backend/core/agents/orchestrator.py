"""
AWIP — AI Data Science Team
Orchestrator Agent

The team lead. Coordinates the specialized agents, manages the MessageBus,
and executes the Iterative Reasoning Loop.

Post-rewire: Only real agents remain. Every phase does genuine computational work.
Agents: Data, Feature, Model, Evaluation, Explainability, Drift, Reporting.
"""

import pandas as pd
from typing import Dict, Any

from .base import MessageBus, BaseAgent
from .data import DataAgent
from .feature import FeatureAgent
from .model import ModelAgent
from .evaluation import EvaluationAgent
from .explainability import ExplainabilityAgent
from .drift import DriftAgent
from .reporting import ReportingAgent

from ..workflow_engine import WorkflowAdaptationEngine
from ..pipeline_executor import PipelineExecutor

class OrchestratorAgent(BaseAgent):
    """Coordinates the AI Data Science Team."""
    
    def __init__(self, message_bus: MessageBus = None):
        if message_bus is None:
            message_bus = MessageBus()
        super().__init__("Orchestrator", message_bus)
        
        # Initialize Team — only agents that do real work
        self.data_agent = DataAgent(self.message_bus)
        self.feature_agent = FeatureAgent(self.message_bus)
        self.model_agent = ModelAgent(self.message_bus)
        self.eval_agent = EvaluationAgent(self.message_bus)
        self.exp_agent = ExplainabilityAgent(self.message_bus)
        self.drift_agent = DriftAgent(self.message_bus)
        self.reporting_agent = ReportingAgent(self.message_bus)
        
        self.workflow_engine = WorkflowAdaptationEngine()
        self.executor = PipelineExecutor()
        
    def run_iterative_loop(self, df: pd.DataFrame, target_col: str, old_df: pd.DataFrame = None, domain_hint: str = "auto-detect") -> Dict[str, Any]:
        """The main iterative reasoning loop.
        
        Pipeline:
          Phase 1: Data Investigation (CUE analysis, quality scoring)
          Phase 2: Drift Detection (KS-test, only if previous dataset exists)
          Phase 3: Feature Engineering (datetime extraction, correlation-based filtering)
          Phase 4: Workflow Design (rule-engine DAG generation)
          Phase 5: Pipeline Execution (sklearn training, cross-validation, leaderboard)
          Phase 6: Model Selection & Tradeoff Analysis
          Phase 7: Failure Mode Analysis (confusion matrix, F1 gaps)
          Phase 8: Explainability (SHAP values, feature importance narratives)
          Phase 9: Executive Report Generation
        """
        
        self.broadcast("Initiating new dataset analysis cycle. Assembling team...")
        
        # Phase 1: Data Investigation
        signals = self.data_agent.execute(df, target_col, domain_hint)
        
        # Phase 2: Drift Detection (only if previous data exists)
        if old_df is not None:
            self.drift_agent.execute(old_df, df, signals.numeric_columns)
            
        # Phase 3: Feature Engineering
        df_enhanced, features = self.feature_agent.execute(df, signals)
        
        # Phase 4: Workflow Design
        self.broadcast("Synthesizing data and feature intelligence to design workflow DAG.")
        workflow = self.workflow_engine.generate_workflow(signals, "expert")
        
        # Phase 5: Pipeline Execution
        self.broadcast(f"Executing workflow v{workflow.version} to gather benchmark metrics.")
        results = self.executor.execute(df_enhanced, workflow, target_col, signals)
        
        # Phase 6: Model Selection & Tradeoffs
        model_insights = self.model_agent.execute(results, signals)
        if "winner" in model_insights and model_insights["winner"] != "Unknown":
            # Update workflow DAG to reflect the winner chosen by Model Agent
            for step in workflow.steps:
                if step.category == "model":
                    step.name = model_insights["winner"]
                    step.reason = model_insights.get("reason", "Selected by Model Agent via benchmarking.")
                    break
        
        # Phase 7: Failure Analysis
        eval_insights = self.eval_agent.execute(results, signals)
        
        # Phase 8: Explainability
        exp_insights = self.exp_agent.execute(results, signals)
        
        # Phase 9: Reporting
        report_data = self.reporting_agent.execute(
            dataset_name=df.name if hasattr(df, 'name') else "Uploaded Dataset",
            task_type=signals.task_type,
            model_results=results,
            features=features
        )
        
        # Final Recommendation
        confidence = 0.90
        if "metrics" in results and "accuracy" in results["metrics"]:
            confidence = max(0.5, results["metrics"]["accuracy"])
        elif "metrics" in results and "r2_score" in results["metrics"]:
            confidence = max(0.5, results["metrics"]["r2_score"])
            
        self.broadcast(f"Pipeline complete. Recommending {workflow.steps[-1].name} with {confidence:.1%} confidence.", confidence=confidence)
        
        return {
            "workflow": workflow,
            "results": results,
            "signals": signals,
            "engineered_features": features,
            "report": report_data,
            "executor": self.executor
        }
