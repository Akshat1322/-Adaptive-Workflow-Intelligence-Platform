"""
AWIP — AI Data Science Team
Drift Agent

Detects, explains, predicts, and recommends actions for data drift
(KS-test analysis, root causes, retraining).
"""

from typing import Dict, Any
import pandas as pd
from .base import BaseAgent, MessageBus
from ..context_engine import ContextUnderstandingEngine

class DriftAgent(BaseAgent):
    """Monitors distribution drift and recommends retraining."""
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("Drift Agent", message_bus)
        self.cue = ContextUnderstandingEngine()
        
    def execute(self, old_df: pd.DataFrame, new_df: pd.DataFrame, numeric_columns: list) -> Dict[str, Any]:
        """Detect drift between two datasets."""
        if old_df is None or new_df is None:
            return {}
            
        self.broadcast("Analyzing dataset for distribution drift compared to previous run...")
        
        drift_results = self.cue.detect_drift(old_df, new_df, numeric_columns)
        
        max_drift = 0.0
        drifted_features = []
        for col, res in drift_results.items():
            if res["drift_score"] > max_drift:
                max_drift = res["drift_score"]
            if res.get("is_drifting", res.get("drift_detected", False)):
                drifted_features.append(col)
                
        if max_drift > 0.2:
            lines = [f"**Significant Drift Detected (Max Score: {max_drift:.2f})**"]
            lines.append(f"Drifted features: {', '.join(drifted_features)}")
            lines.append("\n**Likely Cause:** Data generating process has changed (e.g., new policy, seasonal shift, or demographic change).")
            lines.append("**Recommendation:** Model retraining is highly recommended within the next 2 weeks to prevent performance degradation.")
            report = "\n".join(lines)
            self.broadcast(report, confidence=0.95, metadata={"max_drift": max_drift, "features": drifted_features})
            return {"drift_score": max_drift, "drifted_features": drifted_features, "report": report}
        else:
            self.broadcast(f"Data distributions are stable (Max drift score: {max_drift:.2f}). No retraining necessary.", confidence=0.95)
            return {"drift_score": max_drift, "drifted_features": []}
