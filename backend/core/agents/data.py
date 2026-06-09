"""
AWIP — AI Data Science Team
Data Agent

Responsible for becoming the dataset expert. Performs schema analysis,
missing value analysis, outlier detection, distribution analysis,
and data quality scoring.
"""

import pandas as pd
from typing import Dict, Any

from .base import BaseAgent, MessageBus
# Note: we are importing ContextUnderstandingEngine dynamically or locally if needed
# but it's better to just import it directly from core.context_engine
from ..context_engine import ContextUnderstandingEngine


class DataAgent(BaseAgent):
    """The dataset expert. Analyzes schema, missing values, outliers, and quality."""
    
    def __init__(self, message_bus: MessageBus):
        super().__init__("Data Agent", message_bus)
        self.cue = ContextUnderstandingEngine()
        
    def execute(self, df: pd.DataFrame, target_column: str, domain_hint: str = "auto-detect") -> Any:
        """Analyze the dataset and broadcast findings."""
        self.broadcast("Starting comprehensive dataset analysis...")
        
        # 1. Analyze using Context Engine
        signals = self.cue.analyze(df, target_column, user_intent="", domain_hint=domain_hint)
        
        # 2. Calculate Data Quality Score
        quality_score, issues = self._calculate_quality_score(signals)
        
        # 3. Format report
        report = self._format_report(quality_score, issues, signals)
        
        # 4. Broadcast results
        confidence = 0.95 if quality_score > 70 else 0.85
        self.broadcast(report, confidence=confidence, metadata={
            "quality_score": quality_score,
            "issues": issues,
            "signals": signals  # The raw signals object for other agents to use
        })
        
        return signals
        
    def _calculate_quality_score(self, signals) -> tuple[float, list[str]]:
        """Calculate a 0-100 data quality score and list issues."""
        score = 100.0
        issues = []
        
        if signals.has_missing_values:
            max_miss = max(signals.missing_columns.values())
            penalty = min(30, max_miss * 100)
            score -= penalty
            issues.append(f"Missing values detected (up to {max_miss:.0%} in a column)")
            
        if signals.is_imbalanced:
            score -= 15
            issues.append(f"Severe class imbalance ({signals.imbalance_ratio:.1f}:1)")
            
        if signals.has_outliers:
            score -= 5
            issues.append(f"Outliers detected in {len(signals.outlier_columns)} columns")
            
        if signals.has_multicollinearity:
            score -= 5
            issues.append(f"Multicollinearity ({len(signals.multicollinear_pairs)} correlated pairs)")
            
        if signals.task_type == "unknown":
            score -= 20
            issues.append("Unable to determine task type reliably")
            
        # Target leakage warning heuristic
        if signals.is_high_dimensional:
            issues.append(f"High dimensionality ({signals.n_cols} features) increases overfitting risk")
            
        return max(0.0, score), issues
        
    def _format_report(self, score: float, issues: list[str], signals) -> str:
        lines = [
            f"**Data Quality Score: {score:.0f}%**",
            f"**Shape:** {signals.n_rows:,} rows × {signals.n_cols} cols",
            f"**Task:** {signals.task_type.replace('_', ' ').title()}",
            f"**Domain:** {signals.domain_hint.title() if signals.domain_hint else 'Unknown'}",
        ]
        
        if issues:
            lines.append("\n**Issues Detected:**")
            for issue in issues:
                lines.append(f"- {issue}")
        else:
            lines.append("\n**Issues Detected:** None. Dataset is clean.")
            
        return "\n".join(lines)
