"""
AWIP — AI Data Science Team
Feature Agent 2.0

Responsible for generating features, evaluating their impact via fast
heuristics (correlation/mutual info), rejecting weak features, and
ranking feature usefulness.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any

from dataclasses import dataclass
from .base import BaseAgent, MessageBus

@dataclass
class EngineeredFeature:
    name: str
    source_columns: List[str]
    category: str
    explanation: str
    applied: bool = True

class FeatureAgent(BaseAgent):
    """The Feature Engineering specialist. Evaluates and filters generated features."""
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("Feature Agent", message_bus)
        
    def execute(self, df: pd.DataFrame, signals) -> Tuple[pd.DataFrame, List[EngineeredFeature]]:
        """Generate, evaluate, and filter features."""
        self.broadcast("Starting feature generation and evaluation...")
        
        # 1. Generate features inline
        df_enhanced = df.copy()
        generated_features = []
        
        # Date features
        for col in signals.datetime_columns:
            try:
                df_enhanced[col] = pd.to_datetime(df_enhanced[col])
                df_enhanced[f"{col}_year"] = df_enhanced[col].dt.year
                df_enhanced[f"{col}_month"] = df_enhanced[col].dt.month
                df_enhanced[f"{col}_day"] = df_enhanced[col].dt.day
                df_enhanced[f"{col}_dayofweek"] = df_enhanced[col].dt.dayofweek
                
                generated_features.append(
                    EngineeredFeature(
                        name=f"{col}_parts",
                        source_columns=[col],
                        category="datetime",
                        explanation=f"Extracted year, month, day, and day of week from {col}."
                    )
                )
            except Exception:
                pass
                
        # Numeric interaction features (e.g. ratios if any)
        # Just a simple example: total or ratio if domain allows
        if len(signals.numeric_columns) >= 2 and signals.domain_hint == "hr":
            # Just an example heuristic
            pass
        
        if not generated_features:
            self.broadcast("No feature engineering opportunities detected.")
            return df_enhanced, []
            
        # 2. Evaluate impact (correlation with target)
        target_col = signals.target_column
        if target_col and target_col in df_enhanced.columns and pd.api.types.is_numeric_dtype(df_enhanced[target_col]):
            target = df_enhanced[target_col]
            
            evaluated_features = []
            accepted = []
            rejected = []
            
            for feat in generated_features:
                if not feat.applied:
                    # e.g., encoding recommendations — just pass them through
                    evaluated_features.append(feat)
                    continue
                    
                col_name = feat.name
                if col_name in df_enhanced.columns and pd.api.types.is_numeric_dtype(df_enhanced[col_name]):
                    try:
                        # Fast evaluation: Absolute Pearson correlation
                        corr = abs(df_enhanced[col_name].corr(target))
                        if np.isnan(corr):
                            corr = 0.0
                            
                        # Reject features with near-zero correlation (< 0.01)
                        if corr < 0.01:
                            feat.applied = False
                            feat.explanation += f" [Status: Rejected — Minimal Impact (corr={corr:.3f})]"
                            rejected.append(feat)
                            # Remove from df_enhanced to save memory
                            df_enhanced = df_enhanced.drop(columns=[col_name])
                        else:
                            feat.explanation += f" [Status: Accepted — Impact Score: {corr:.3f}]"
                            accepted.append((feat, corr))
                    except Exception:
                        accepted.append((feat, 0.0))
                else:
                    # Non-numeric engineered feature (rare), just accept
                    accepted.append((feat, 0.0))
                    
            # Sort accepted by impact
            accepted.sort(key=lambda x: x[1], reverse=True)
            evaluated_features.extend([f[0] for f in accepted])
            evaluated_features.extend(rejected)
            
            # Format report
            lines = [f"**Feature Generation Complete**"]
            lines.append(f"Generated: {len(generated_features)}")
            lines.append(f"Accepted: {len(accepted)}")
            lines.append(f"Rejected: {len(rejected)}")
            
            if accepted:
                lines.append("\n**Top Features:**")
                for feat, score in accepted[:3]:
                    lines.append(f"- **{feat.name}** (Impact: {score:.3f}): {feat.explanation.split(' [Status')[0]}")
                    
            if rejected:
                lines.append(f"\n*Rejected {len(rejected)} weak feature(s) to prevent noise.*")
                
            report = "\n".join(lines)
            self.broadcast(report, confidence=0.90, metadata={"features": evaluated_features})
            
            return df_enhanced, evaluated_features
            
        else:
            # Cannot calculate correlation (e.g. classification target is string and unencoded)
            # Accept all generated features that are applied
            applied_count = sum(1 for f in generated_features if f.applied)
            report = f"Generated **{applied_count}** new features based on domain heuristics. Target is non-numeric; bypassed quantitative rejection step."
            self.broadcast(report, confidence=0.80, metadata={"features": generated_features})
            
            return df_enhanced, generated_features
