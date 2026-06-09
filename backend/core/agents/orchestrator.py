"""
AWIP — AI Data Science Team
Orchestrator Agent

The team lead. Coordinates the specialized agents, manages the MessageBus,
and executes the Iterative Reasoning Loop. Replaces the old monolithic
OrchestratorAgent.
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
from .research import ResearchAgent
from .deployment import DeploymentAgent
from .reporting import ReportingAgent
from .monitoring import MonitoringAgent

from ..workflow_engine import WorkflowAdaptationEngine
from ..pipeline_executor import PipelineExecutor

class OrchestratorAgent(BaseAgent):
    """Coordinates the AI Data Science Team."""
    
    def __init__(self, message_bus: MessageBus = None):
        if message_bus is None:
            message_bus = MessageBus()
        super().__init__("Orchestrator", message_bus)
        
        # Initialize Team
        self.data_agent = DataAgent(self.message_bus)
        self.feature_agent = FeatureAgent(self.message_bus)
        self.model_agent = ModelAgent(self.message_bus)
        self.eval_agent = EvaluationAgent(self.message_bus)
        self.exp_agent = ExplainabilityAgent(self.message_bus)
        self.drift_agent = DriftAgent(self.message_bus)
        self.research_agent = ResearchAgent(self.message_bus)
        self.deployment_agent = DeploymentAgent(self.message_bus)
        self.reporting_agent = ReportingAgent(self.message_bus)
        self.monitoring_agent = MonitoringAgent(self.message_bus)
        
        self.workflow_engine = WorkflowAdaptationEngine()
        self.executor = PipelineExecutor()
        
    def run_iterative_loop(self, df: pd.DataFrame, target_col: str, old_df: pd.DataFrame = None, domain_hint: str = "auto-detect") -> Dict[str, Any]:
        """The main iterative reasoning loop."""
        
        self.broadcast("Initiating new dataset analysis cycle. Assembling team...")
        
        # Phase 1: Data Investigation
        signals = self.data_agent.execute(df, target_col, domain_hint)
        
        if old_df is not None:
            self.drift_agent.execute(old_df, df, signals.numeric_columns)
            
        # Phase 2: Feature Engineering
        df_enhanced, features = self.feature_agent.execute(df, signals)
        
        # Phase 3: Orchestrator reasoning (Workflow Design)
        self.broadcast("Synthesizing data and feature intelligence to design workflow DAG.")
        workflow = self.workflow_engine.generate_workflow(signals, "expert")
        
        # Phase 4: Experiment (Execution)
        self.broadcast(f"Executing workflow v{workflow.version} to gather benchmark metrics.")
        results = self.executor.execute(df_enhanced, workflow, target_col, signals)
        
        # Phase 5: Model Selection & Tradeoffs
        model_insights = self.model_agent.execute(results, signals)
        if "winner" in model_insights and model_insights["winner"] != "Unknown":
            # Update workflow DAG to reflect the winner chosen by Model Agent
            for step in workflow.steps:
                if step.category == "model":
                    step.name = model_insights["winner"]
                    step.reason = model_insights.get("reason", "Selected by Model Agent via benchmarking.")
                    break
        
        # Phase 6: Failure Analysis
        eval_insights = self.eval_agent.execute(results, signals)
        
        # Phase 7: Explainability
        exp_insights = self.exp_agent.execute(results, signals)
        
        # Phase 8: Research & Best Practices
        research_insights = self.research_agent.execute(signals, workflow, results)
        
        # Phase 9: Reporting
        report_data = self.reporting_agent.execute(
            dataset_name=df.name if hasattr(df, 'name') else "Uploaded Dataset",
            task_type=signals.task_type,
            model_results=results,
            features=features
        )
        
        # Phase 10: Deployment & Monitoring
        model_package = self.deployment_agent.execute(df, target_col, results)
        monitoring_status = self.monitoring_agent.execute(model_package, df)
        
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
