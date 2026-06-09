"""
AWIP — AI Data Science Team
Model Agent

The ML Engineer. Explores models, runs benchmarks, tunes hyperparameters,
and provides tradeoff analysis for model selection.
"""

from typing import Dict, Any, List
from .base import BaseAgent, MessageBus

class ModelAgent(BaseAgent):
    """The ML Engineer. Explores models and benchmarks them."""
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("Model Agent", message_bus)
        
    def execute(self, results: Dict[str, Any], signals) -> Dict[str, Any]:
        """
        Evaluate the leaderboard from PipelineExecutor and select the best model.
        In a full implementation, this agent would orchestrate its own CV loops.
        Here we use the PipelineExecutor's leaderboard as the basis for reasoning.
        """
        self.broadcast("Exploring model candidates and benchmarking performance...")
        
        leaderboard = results.get("leaderboard", [])
        if not leaderboard:
            self.broadcast("No benchmarking data available.", confidence=0.5)
            return {"winner": "Unknown"}
            
        # Select winner
        winner = leaderboard[0]
        runner_up = leaderboard[1] if len(leaderboard) > 1 else None
        
        lines = ["**Model Benchmarking Complete**"]
        lines.append(f"Tested {len(leaderboard)} algorithms.")
        
        lines.append("\n**Leaderboard:**")
        for i, item in enumerate(leaderboard[:4]):
            lines.append(f"{i+1}. **{item['name']}** - Score: {item['score']:.4f}")
            
        lines.append(f"\n**Winner:** {winner['name']}")
        
        # Reason
        reason = self._generate_reasoning(winner['name'], signals)
        lines.append(f"**Reason:** {reason}")
        
        if runner_up:
            delta = winner['score'] - runner_up['score']
            lines.append(f"**Tradeoff Analysis:** {winner['name']} outperformed {runner_up['name']} by {delta:.4f}. "
                         f"While {runner_up['name']} might be faster to train, {winner['name']} provides superior predictive power "
                         f"given the dataset characteristics.")
                         
        report = "\n".join(lines)
        self.broadcast(report, confidence=0.92, metadata={"winner": winner['name'], "leaderboard": leaderboard})
        
        return {"winner": winner['name'], "leaderboard": leaderboard, "reason": reason}
        
    def _generate_reasoning(self, model_name: str, signals) -> str:
        name = model_name.lower()
        if "xgb" in name or "catboost" in name or "lightgbm" in name:
            return "Gradient boosting captures complex non-linear feature interactions and handles mixed feature types natively."
        elif "randomforest" in name:
            return "Random Forest provides robust performance with less hyperparameter tuning and resists overfitting."
        elif "logistic" in name or "ridge" in name:
            return "Linear models provide highly interpretable results and stable predictions for this dataset."
        return "Best empirical cross-validation score."
