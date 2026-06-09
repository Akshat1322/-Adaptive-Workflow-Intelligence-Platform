"""
AWIP — Adaptive Workflow Intelligence Platform
Workflow Adaptation Engine (WAE)

The CORE differentiator. Dynamically mutates workflows based on context signals
using a hybrid rule-engine + LLM reasoning architecture.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json

from .llm_engine import LLMEngine


@dataclass
class WorkflowStep:
    """A single step in the workflow pipeline."""
    id: str
    name: str
    category: str  # preprocessing, sampling, model, explainability, evaluation
    params: Dict = field(default_factory=dict)
    reason: str = ""
    added_by: str = "system"  # system, user, adaptation


@dataclass
class WorkflowDAG:
    """Directed Acyclic Graph representing the full workflow."""
    version: int = 1
    steps: List[WorkflowStep] = field(default_factory=list)
    adaptations: List[Dict] = field(default_factory=list)
    evolution_log: List[Dict] = field(default_factory=list)
    task_type: str = "unknown"
    explanation: str = ""
    metadata: Dict = field(default_factory=dict)

    def get_step_names(self) -> List[str]:
        return [s.name for s in self.steps]

    def get_pipeline_description(self) -> str:
        return " → ".join(self.get_step_names())

    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "steps": [
                {"id": s.id, "name": s.name, "category": s.category,
                 "params": s.params, "reason": s.reason}
                for s in self.steps
            ],
            "adaptations": self.adaptations,
            "task_type": self.task_type,
            "explanation": self.explanation,
        }


class WorkflowAdaptationEngine:
    """
    Core engine that generates and adapts workflow DAGs based on context signals.
    Uses deterministic rules for well-known patterns and generates explanations.
    """

    def generate_workflow(self, signals, user_level: str = "intermediate") -> WorkflowDAG:
        """Generate a complete workflow from context signals."""
        dag = WorkflowDAG()
        dag.task_type = signals.task_type

        # Phase 1: Apply deterministic adaptation rules
        self._apply_missing_value_rules(signals, dag)
        self._apply_encoding_rules(signals, dag)
        self._apply_scaling_rules(signals, dag)
        self._apply_dimensionality_rules(signals, dag)
        self._apply_imbalance_rules(signals, dag)
        self._apply_model_rules(signals, dag, user_level)
        self._apply_explainability_rules(signals, dag, user_level)

        # Generate overall explanation (Rule-based primary)
        dag.explanation = self._generate_workflow_explanation(signals, dag, user_level)
        
        # Override with LLM explanation if available
        try:
            llm = LLMEngine()
            llm_exp = llm.reason_about_workflow(signals, dag.steps, user_level)
            if llm_exp and not llm_exp.startswith("[Fallback") and not llm_exp.startswith("[LLM Error"):
                # Use the rule-based one as base, append LLM insight if we want,
                # but llm_engine already handles fallbacks perfectly now.
                # Since we updated llm_engine to return excellent rule-based fallbacks,
                # we can just use llm_exp directly!
                dag.explanation = llm_exp
        except Exception:
            pass

        return dag

    def adapt_workflow(self, old_dag: WorkflowDAG, new_signals, user_level: str = "intermediate") -> WorkflowDAG:
        """Adapt an existing workflow based on new context signals."""
        new_dag = self.generate_workflow(new_signals, user_level)
        new_dag.version = old_dag.version + 1

        # Compute evolution diff
        old_names = set(old_dag.get_step_names())
        new_names = set(new_dag.get_step_names())

        added = new_names - old_names
        removed = old_names - new_names

        evolution = []
        for step in new_dag.steps:
            if step.name in added:
                evolution.append({
                    "type": "added",
                    "step": step.name,
                    "reason": step.reason,
                    "icon": "🟢"
                })

        for name in removed:
            old_step = next((s for s in old_dag.steps if s.name == name), None)
            evolution.append({
                "type": "removed",
                "step": name,
                "reason": f"No longer needed based on new data characteristics",
                "icon": "🔴"
            })

        # Check for replacements (same category, different method)
        for old_step in old_dag.steps:
            for new_step in new_dag.steps:
                if (old_step.category == new_step.category and
                    old_step.name != new_step.name and
                    old_step.name in removed and new_step.name in added):
                    # This is a replacement
                    evolution = [e for e in evolution if e["step"] not in (old_step.name, new_step.name)]
                    evolution.append({
                        "type": "replaced",
                        "old_step": old_step.name,
                        "new_step": new_step.name,
                        "reason": new_step.reason,
                        "icon": "🔄"
                    })

        new_dag.evolution_log = evolution
        return new_dag

    # ── RULE METHODS ──────────────────────────────────────────

    def _apply_missing_value_rules(self, signals, dag: WorkflowDAG):
        """Add imputation if missing values detected."""
        if not signals.has_missing_values:
            return

        max_missing = max(signals.missing_columns.values()) if signals.missing_columns else 0
        n_missing_cols = len(signals.missing_columns)

        if max_missing > 0.3:
            # Heavy missing — use iterative imputer
            dag.steps.append(WorkflowStep(
                id="impute",
                name="IterativeImputer",
                category="preprocessing",
                params={"max_iter": 10, "random_state": 42},
                reason=f"{n_missing_cols} columns have missing values (max {max_missing:.0%}). "
                       f"Iterative imputation selected because missingness exceeds 30%, "
                       f"requiring multivariate imputation that preserves feature relationships."
            ))
            dag.adaptations.append({
                "signal": "heavy_missing_values",
                "action": "added_iterative_imputer",
                "detail": f"Max missing ratio: {max_missing:.0%}"
            })
        else:
            # Moderate missing — KNN imputer
            dag.steps.append(WorkflowStep(
                id="impute",
                name="KNNImputer",
                category="preprocessing",
                params={"n_neighbors": 5},
                reason=f"{n_missing_cols} columns have missing values (max {max_missing:.0%}). "
                       f"KNN imputation preserves local data structure by using similar samples "
                       f"to estimate missing values."
            ))
            dag.adaptations.append({
                "signal": "missing_values",
                "action": "added_knn_imputer",
                "detail": f"Max missing ratio: {max_missing:.0%}"
            })

    def _apply_encoding_rules(self, signals, dag: WorkflowDAG):
        """Add encoding for categorical features."""
        if not signals.categorical_columns:
            return

        if signals.has_high_cardinality:
            dag.steps.append(WorkflowStep(
                id="encode",
                name="TargetEncoder",
                category="preprocessing",
                params={"smoothing": 0.3},
                reason=f"{len(signals.categorical_columns)} categorical columns detected "
                       f"({len(signals.high_cardinality_columns)} with high cardinality > 50). "
                       f"Target encoding selected over one-hot to avoid dimensionality explosion."
            ))
            dag.adaptations.append({
                "signal": "high_cardinality_categoricals",
                "action": "added_target_encoder",
            })
        else:
            dag.steps.append(WorkflowStep(
                id="encode",
                name="OrdinalEncoder",
                category="preprocessing",
                params={"handle_unknown": "use_encoded_value", "unknown_value": -1},
                reason=f"{len(signals.categorical_columns)} categorical columns with low cardinality. "
                       f"Ordinal encoding is efficient and sufficient for tree-based models."
            ))
            dag.adaptations.append({
                "signal": "categorical_features",
                "action": "added_ordinal_encoder",
            })

    def _apply_scaling_rules(self, signals, dag: WorkflowDAG):
        """Add appropriate scaler based on data characteristics."""
        if not signals.numeric_columns:
            return

        # Skip scaling for pure tree-based models if no other reason
        if signals.task_type in ("binary_classification", "multiclass_classification", "regression"):
            if signals.has_outliers:
                dag.steps.append(WorkflowStep(
                    id="scale",
                    name="RobustScaler",
                    category="preprocessing",
                    params={},
                    reason=f"Outliers detected in {len(signals.outlier_columns)} columns "
                           f"({', '.join(signals.outlier_columns[:3])}). RobustScaler uses "
                           f"median and IQR, making it resistant to extreme values."
                ))
                dag.adaptations.append({
                    "signal": "outliers_detected",
                    "action": "added_robust_scaler",
                })
            else:
                dag.steps.append(WorkflowStep(
                    id="scale",
                    name="StandardScaler",
                    category="preprocessing",
                    params={},
                    reason=f"Standard scaling applied to {len(signals.numeric_columns)} numeric features "
                           f"for consistent feature ranges. No significant outliers detected."
                ))

    def _apply_dimensionality_rules(self, signals, dag: WorkflowDAG):
        """Add dimensionality reduction if needed."""
        if signals.is_high_dimensional:
            dag.steps.append(WorkflowStep(
                id="dim_reduce",
                name="PCA",
                category="preprocessing",
                params={"n_components": 0.95},
                reason=f"Dataset has {signals.n_cols} features (high-dimensional). "
                       f"PCA added to reduce dimensionality while retaining 95% of variance. "
                       f"This reduces overfitting risk and training time."
            ))
            dag.adaptations.append({
                "signal": "high_dimensionality",
                "action": "added_pca",
                "detail": f"{signals.n_cols} features"
            })

        if signals.has_multicollinearity:
            dag.adaptations.append({
                "signal": "multicollinearity",
                "action": "flagged_correlated_features",
                "detail": f"{len(signals.multicollinear_pairs)} pairs with correlation > 0.9"
            })

    def _apply_imbalance_rules(self, signals, dag: WorkflowDAG):
        """Add resampling for imbalanced datasets."""
        if not signals.is_imbalanced:
            return

        if signals.imbalance_ratio > 10:
            dag.steps.append(WorkflowStep(
                id="resample",
                name="SMOTE + Tomek",
                category="sampling",
                params={"sampling_strategy": 0.5},
                reason=f"Severe class imbalance ({signals.imbalance_ratio:.1f}:1). "
                       f"SMOTE generates synthetic minority samples, Tomek links removes "
                       f"borderline majority samples for cleaner decision boundaries."
            ))
        else:
            dag.steps.append(WorkflowStep(
                id="resample",
                name="SMOTE",
                category="sampling",
                params={"sampling_strategy": 0.8},
                reason=f"Class imbalance detected ({signals.imbalance_ratio:.1f}:1). "
                       f"SMOTE oversampling added to balance class representation "
                       f"and prevent model bias toward the majority class."
            ))

        dag.adaptations.append({
            "signal": "class_imbalance",
            "action": "added_smote",
            "detail": f"Ratio: {signals.imbalance_ratio:.1f}:1"
        })

    def _apply_model_rules(self, signals, dag: WorkflowDAG, user_level: str):
        """Select the most appropriate model based on all signals."""
        task = signals.task_type
        n_rows = signals.n_rows
        has_categorical = len(signals.categorical_columns) > 0

        if task == "binary_classification" or task == "multiclass_classification":
            model = self._select_classification_model(signals, user_level)
        elif task == "regression":
            model = self._select_regression_model(signals, user_level)
        elif task == "time_series_forecasting":
            model = WorkflowStep(
                id="model",
                name="ARIMA + XGBoost Ensemble",
                category="model",
                params={"arima_order": "auto", "xgb_n_estimators": 300},
                reason="Time-series task detected. Ensemble of ARIMA (captures linear trends/seasonality) "
                       "and XGBoost (captures non-linear patterns with lag features)."
            )
        elif task == "clustering":
            model = WorkflowStep(
                id="model",
                name="KMeans + DBSCAN",
                category="model",
                params={"kmeans_n_clusters": "auto", "dbscan_eps": "auto"},
                reason="Clustering task — KMeans for well-separated clusters, "
                       "DBSCAN for density-based and noise-robust clustering."
            )
        elif task == "anomaly_detection":
            model = WorkflowStep(
                id="model",
                name="IsolationForest",
                category="model",
                params={"n_estimators": 200, "contamination": 0.05},
                reason="Anomaly detection task. Isolation Forest excels at identifying outliers "
                       "by isolating anomalies through random partitioning."
            )
        elif task == "nlp_classification":
            model = WorkflowStep(
                id="model",
                name="TF-IDF + LightGBM",
                category="model",
                params={"max_features": 10000, "n_estimators": 300},
                reason="NLP task detected. TF-IDF vectorization combined with LightGBM "
                       "provides strong text classification with fast training."
            )
        else:
            model = WorkflowStep(
                id="model",
                name="RandomForest",
                category="model",
                params={"n_estimators": 200, "random_state": 42},
                reason="Task type uncertain — Random Forest selected as a robust default "
                       "that handles mixed feature types and is resistant to overfitting."
            )

        dag.steps.append(model)

    def _select_classification_model(self, signals, user_level: str) -> WorkflowStep:
        """Select optimal classification model."""
        n_rows = signals.n_rows
        n_cols = signals.n_cols
        has_cat = len(signals.categorical_columns) > 0
        is_imb = signals.is_imbalanced

        # For beginners, prefer simpler models
        if user_level == "beginner" and n_rows < 10000:
            return WorkflowStep(
                id="model", name="RandomForest", category="model",
                params={"n_estimators": 200, "random_state": 42,
                        "class_weight": "balanced" if is_imb else None},
                reason="Random Forest selected — robust, interpretable, and handles mixed features well. "
                       "Good default for understanding feature importance."
            )

        # Large dataset with mixed features → XGBoost
        if n_rows > 5000 or has_cat or is_imb:
            params = {"n_estimators": 500, "learning_rate": 0.05, "max_depth": 6}
            if is_imb:
                params["scale_pos_weight"] = round(signals.imbalance_ratio, 1)
            return WorkflowStep(
                id="model", name="XGBoost", category="model",
                params=params,
                reason=f"XGBoost selected: handles {'mixed feature types' if has_cat else 'numeric features'} natively, "
                       f"{'class imbalance via scale_pos_weight, ' if is_imb else ''}"
                       f"{'large dataset benefits from gradient boosting efficiency, ' if n_rows > 5000 else ''}"
                       f"and captures non-linear feature interactions."
            )

        # Small, clean dataset → Logistic Regression
        if n_rows < 5000 and n_cols < 30 and not has_cat:
            return WorkflowStep(
                id="model", name="LogisticRegression", category="model",
                params={"max_iter": 1000, "C": 1.0,
                        "class_weight": "balanced" if is_imb else None},
                reason="Small, clean numeric dataset — Logistic Regression provides "
                       "interpretable results with fast training."
            )

        # Default
        return WorkflowStep(
            id="model", name="LightGBM", category="model",
            params={"n_estimators": 300, "learning_rate": 0.05},
            reason="LightGBM selected for fast training, memory efficiency, "
                   "and strong performance on tabular data."
        )

    def _select_regression_model(self, signals, user_level: str) -> WorkflowStep:
        """Select optimal regression model."""
        n_rows = signals.n_rows

        if n_rows < 5000 and signals.n_cols < 30:
            return WorkflowStep(
                id="model", name="Ridge Regression", category="model",
                params={"alpha": 1.0},
                reason="Small numeric dataset — Ridge Regression with L2 regularization "
                       "provides stable predictions and prevents overfitting."
            )

        return WorkflowStep(
            id="model", name="XGBoost Regressor", category="model",
            params={"n_estimators": 500, "learning_rate": 0.05, "max_depth": 6},
            reason=f"XGBoost Regressor selected for {signals.n_rows:,} row dataset — "
                   f"captures non-linear relationships and handles mixed feature types."
        )

    def _apply_explainability_rules(self, signals, dag: WorkflowDAG, user_level: str):
        """Add explainability based on model type and user level."""
        model_step = next((s for s in dag.steps if s.category == "model"), None)
        if not model_step:
            return

        tree_models = {"XGBoost", "RandomForest", "LightGBM", "XGBoost Regressor",
                       "IsolationForest", "TF-IDF + LightGBM"}

        if model_step.name in tree_models:
            method = "SHAP (TreeExplainer)"
        else:
            method = "SHAP (KernelExplainer)"

        if user_level == "beginner":
            dag.steps.append(WorkflowStep(
                id="explain",
                name="Feature Importance + Simple SHAP",
                category="explainability",
                params={"method": method, "plot_type": "bar", "top_n": 10},
                reason="Feature importance bar chart and simplified SHAP summary "
                       "for easy-to-understand model explanations."
            ))
        else:
            dag.steps.append(WorkflowStep(
                id="explain",
                name="SHAP Analysis",
                category="explainability",
                params={"method": method, "plot_type": "summary", "show_interactions": True},
                reason="Full SHAP analysis with summary plots and interaction effects "
                       "for detailed model interpretability."
            ))

    def _generate_workflow_explanation(self, signals, dag: WorkflowDAG, user_level: str) -> str:
        """Generate a natural language explanation of the complete workflow."""
        steps_desc = dag.get_pipeline_description()
        n_adaptations = len(dag.adaptations)

        if user_level == "beginner":
            explanation = (
                f"I've designed a {len(dag.steps)}-step workflow for your data:\n\n"
                f"**Pipeline:** {steps_desc}\n\n"
                f"Here's the simple version of why:\n"
            )
            for step in dag.steps:
                short_reason = step.reason.split(".")[0] + "."
                explanation += f"- **{step.name}**: {short_reason}\n"
        else:
            explanation = (
                f"**Adaptive Workflow v{dag.version}** — {len(dag.steps)} stages, "
                f"{n_adaptations} signal-driven adaptations\n\n"
                f"**Pipeline:** `{steps_desc}`\n\n"
                f"**Detailed Reasoning:**\n"
            )
            for step in dag.steps:
                explanation += f"- **{step.name}** [{step.category}]: {step.reason}\n"

            if dag.adaptations:
                explanation += f"\n**Adaptations Applied ({n_adaptations}):**\n"
                for a in dag.adaptations:
                    explanation += f"- Signal: `{a['signal']}` → Action: `{a['action']}`"
                    if "detail" in a:
                        explanation += f" ({a['detail']})"
                    explanation += "\n"

        return explanation

    def get_evolution_summary(self, dag: WorkflowDAG) -> str:
        """Generate a readable summary of workflow evolution."""
        if not dag.evolution_log:
            return "This is the initial workflow version. No prior evolution."

        lines = [f"### Workflow Evolution: v{dag.version - 1} → v{dag.version}\n"]

        for entry in dag.evolution_log:
            if entry["type"] == "added":
                lines.append(f"  {entry['icon']} **Added** `{entry['step']}`: {entry['reason']}")
            elif entry["type"] == "removed":
                lines.append(f"  {entry['icon']} **Removed** `{entry['step']}`: {entry['reason']}")
            elif entry["type"] == "replaced":
                lines.append(
                    f"  {entry['icon']} **Replaced** `{entry['old_step']}` → `{entry['new_step']}`: {entry['reason']}"
                )

        return "\n".join(lines)
