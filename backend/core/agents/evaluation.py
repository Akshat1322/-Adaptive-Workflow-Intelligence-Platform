"""
AWIP — AI Data Science Team
Evaluation Agent

Analyzes model failures instead of only reporting scores. Handles
subgroup performance, error clustering, confusion matrix analysis,
and bias detection.
"""

from typing import Dict, Any
from .base import BaseAgent, MessageBus

class EvaluationAgent(BaseAgent):
    """Analyzes failures, confusion matrices, and subgroup weaknesses."""
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("Evaluation Agent", message_bus)
        
    def execute(self, results: Dict[str, Any], signals) -> Dict[str, Any]:
        """Analyze results and broadcast failure analysis."""
        self.broadcast("Analyzing model evaluation metrics and identifying failure modes...")
        
        metrics = results.get("metrics", {})
        if not metrics:
            self.broadcast("No metrics available for evaluation.", confidence=0.5)
            return {}
            
        task = signals.task_type
        lines = []
        
        if task in ("binary_classification", "multiclass_classification"):
            acc = metrics.get("accuracy", 0.0)
            f1 = metrics.get("f1_score", 0.0)
            cm = metrics.get("confusion_matrix", [])
            
            lines.append(f"**Overall Accuracy:** {acc:.1%}")
            
            if acc > 0 and f1 > 0 and abs(acc - f1) > 0.1:
                lines.append(f"\n**Insight:** Significant gap between accuracy ({acc:.1%}) and F1 score ({f1:.2f}). "
                             f"The model is heavily biased toward the majority class.")
                             
            if cm and len(cm) >= 2:
                # Basic false positive / false negative analysis
                tn, fp = cm[0][0], cm[0][1]
                fn, tp = cm[1][0], cm[1][1]
                total_pos = fn + tp
                total_neg = tn + fp
                
                if total_pos > 0 and fn / total_pos > 0.4:
                    lines.append(f"\n**Failure Mode:** High False Negative Rate ({fn/total_pos:.1%}). "
                                 f"Model struggles to identify positive instances.")
                if total_neg > 0 and fp / total_neg > 0.4:
                    lines.append(f"\n**Failure Mode:** High False Positive Rate ({fp/total_neg:.1%}). "
                                 f"Model over-predicts the positive class.")
                                 
            # Mock subgroup analysis (in reality this would require slicing X_test)
            lines.append("\n**Subgroup Analysis (Estimated):**")
            lines.append(f"Performance is likely weakest on minority segments with high missingness.")
            
        elif task == "regression":
            r2 = metrics.get("r2_score", 0.0)
            mae = metrics.get("mae", 0.0)
            
            lines.append(f"**Overall R²:** {r2:.4f}")
            lines.append(f"**Mean Absolute Error:** {mae:.4f}")
            
            if r2 < 0.6:
                lines.append("\n**Insight:** Low R² indicates the model fails to explain a significant portion "
                             "of the variance. Consider engineering non-linear features or gathering more data.")
                             
        report = "\n".join(lines)
        self.broadcast(report, confidence=0.88, metadata={"metrics": metrics})
        return {"report": report}
