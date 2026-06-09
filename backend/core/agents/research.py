"""
AWIP — AI Data Science Team
Research Agent

Provides external intelligence, best practices, algorithm recommendations,
and summarizes common approaches. Replaces core/research_notes.py.
"""

from typing import Dict, Any
from .base import BaseAgent, MessageBus
from ..llm_engine import LLMEngine
import json

class ResearchAgent(BaseAgent):
    """Provides external intelligence and synthesizes findings."""
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("Research Agent", message_bus)
        self.llm = LLMEngine()
        
    def execute(self, signals, workflow_dag, results) -> Dict[str, Any]:
        """Generate research intelligence based on the pipeline."""
        self.broadcast("Retrieving external intelligence and best practices for this task...")
        
        # We can use the LLM to generate a quick JSON summary of best practices
        task = signals.task_type
        domain = signals.domain_hint
        
        prompt = f"""
        You are an AI Research Agent. The team is solving a {task} problem in the {domain} domain.
        Provide 3 bullet points of best practices for this exact type of dataset.
        Format as a JSON list of strings.
        """
        
        best_practices = []
        try:
            resp = self.llm.generate(prompt, max_tokens=200)
            # Find JSON array
            start = resp.find("[")
            end = resp.rfind("]") + 1
            if start != -1 and end != -1:
                best_practices = json.loads(resp[start:end])
        except Exception:
            # Fallback
            best_practices = [
                "Tree-based models (XGBoost/LightGBM) often outperform deep learning on tabular data.",
                "Always check for target leakage when generating features.",
                "Use SHAP for consistent feature attribution."
            ]
            
        if not best_practices:
            best_practices = ["Analyze feature correlations to understand redundancy.", "Monitor for data drift in production."]
            
        lines = ["**External Intelligence & Best Practices:**"]
        for bp in best_practices:
            lines.append(f"- {bp}")
            
        report = "\n".join(lines)
        self.broadcast(report, confidence=0.85)
        return {"best_practices": best_practices, "report": report}
