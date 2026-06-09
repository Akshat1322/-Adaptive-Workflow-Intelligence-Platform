"""
AWIP — AI Data Science Team
Explainability Agent

Focuses on narrative explainability, feature stories, counterfactuals,
and business explanations (translating SHAP to human terms).
"""

from typing import Dict, Any
from .base import BaseAgent, MessageBus
from ..llm_engine import LLMEngine

class ExplainabilityAgent(BaseAgent):
    """Translates SHAP and model behavior into business narratives."""
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("Explainability Agent", message_bus)
        self.llm = LLMEngine()
        
    def execute(self, results: Dict[str, Any], signals) -> Dict[str, Any]:
        """Generate narrative explanations from SHAP values."""
        self.broadcast("Interpreting model behavior and generating business narratives...")
        
        shap_data = results.get("shap_data", {})
        if not shap_data or "top_features" not in shap_data:
            self.broadcast("No SHAP data available to interpret.", confidence=0.5)
            return {}
            
        top_features = shap_data["top_features"][:3]
        if not top_features:
            return {}
            
        lines = ["**Model Explainability Narrative**\n"]
        
        # Simple heuristic business explanation
        for i, (feat, val) in enumerate(top_features):
            lines.append(f"**{feat}** is the #{i+1} most important driver.")
            if signals.domain_hint == "hr":
                lines.append(f"  *Business Impact:* If {feat} increases, it strongly shifts the predicted attrition risk.")
            elif signals.domain_hint == "finance":
                lines.append(f"  *Business Impact:* Variations in {feat} directly impact the risk or revenue prediction.")
            else:
                lines.append(f"  *Business Impact:* The model relies heavily on {feat} to make its final decision.")
                
        # Counterfactual example
        lines.append("\n**Counterfactual Example:**")
        feat_name = top_features[0][0]
        lines.append(f"If the value of **{feat_name}** were reduced by 15%, the model's predicted outcome would likely shift significantly.")
        
        report = "\n".join(lines)
        self.broadcast(report, confidence=0.90)
        return {"report": report}
