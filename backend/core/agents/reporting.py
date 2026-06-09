from typing import Dict, Any, List
import pandas as pd
from .base import BaseAgent, MessageBus

class ReportingAgent(BaseAgent):
    """
    Reporting Agent: Generates structured executive and technical reports based on experiment outcomes.
    """
    
    def __init__(self, message_bus: MessageBus):
        super().__init__(name="Reporting Agent", message_bus=message_bus)
        
    def execute(self, dataset_name: str, task_type: str, model_results: Dict[str, Any], features: List[str]) -> Dict[str, str]:
        """
        Synthesizes a report.
        """
        self.broadcast("Compiling executive and technical reports...", confidence=0.88)
        
        leaderboard = model_results.get("leaderboard", [])
        winner = model_results.get("winner_model") or (leaderboard[0]["name"] if leaderboard else "Unknown")
        metrics = model_results.get("metrics", {})
        score = metrics.get("accuracy", metrics.get("r2_score", leaderboard[0]["score"] if leaderboard else 0.0))
        
        metric_label = "accuracy" if "accuracy" in metrics else "r2_score" if "r2_score" in metrics else "score"
        metric_value = metrics.get(metric_label, score)

        report_content = f"# Executive Summary\n\nDataset: {dataset_name}\nTask: {task_type}\n\n"
        report_content += f"## Findings\nThe Orchestrator successfully built a pipeline. The best performing model was **{winner}** with a {metric_label.replace('_', ' ')} of **{metric_value:.4f}**.\n\n"
        report_content += f"## Feature Engineering\nThe Feature Agent engineered {len(features)} new features which contributed to this performance.\n\n"
        if leaderboard:
            report_content += "## Model Leaderboard\n"
            for i, item in enumerate(leaderboard[:5], 1):
                report_content += f"- {i}. **{item['name']}**: {item['score']:.4f}\n"
            report_content += "\n"
        
        self.broadcast("Report generated successfully.", confidence=0.95, metadata={"report_length": len(report_content)})
        
        return {
            "markdown": report_content,
            "status": "ready"
        }
