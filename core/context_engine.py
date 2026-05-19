"""
AWIP — Adaptive Workflow Intelligence Platform
Context Understanding Engine (CUE)

Analyzes dataset characteristics, infers task types, detects data quality issues,
and generates structured context signals for the Workflow Adaptation Engine.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from scipy import stats


@dataclass
class ContextSignals:
    """Structured representation of all dataset context signals."""
    n_rows: int = 0
    n_cols: int = 0
    missing_columns: Dict[str, float] = field(default_factory=dict)
    overall_missing_ratio: float = 0.0
    numeric_columns: List[str] = field(default_factory=list)
    categorical_columns: List[str] = field(default_factory=list)
    text_columns: List[str] = field(default_factory=list)
    datetime_columns: List[str] = field(default_factory=list)
    boolean_columns: List[str] = field(default_factory=list)
    target_column: Optional[str] = None
    task_type: str = "unknown"
    imbalance_ratio: float = 1.0
    is_imbalanced: bool = False
    has_missing_values: bool = False
    has_outliers: bool = False
    outlier_columns: List[str] = field(default_factory=list)
    has_high_cardinality: bool = False
    high_cardinality_columns: List[str] = field(default_factory=list)
    has_time_column: bool = False
    has_text_column: bool = False
    is_high_dimensional: bool = False
    is_large_dataset: bool = False
    multicollinear_pairs: List[Tuple[str, str]] = field(default_factory=list)
    has_multicollinearity: bool = False
    domain_hint: str = "general"
    dataset_size_class: str = "small"
    numeric_summary: Dict = field(default_factory=dict)
    class_distribution: Dict = field(default_factory=dict)
    feature_types_summary: Dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    def get_summary_text(self) -> str:
        """Generate a human-readable summary of dataset characteristics."""
        lines = [
            f"📊 **Dataset Overview:** {self.n_rows:,} rows × {self.n_cols} columns",
            f"  • Numeric: {len(self.numeric_columns)} | Categorical: {len(self.categorical_columns)} | "
            f"Text: {len(self.text_columns)} | DateTime: {len(self.datetime_columns)}",
        ]
        if self.target_column:
            lines.append(f"  • Target: `{self.target_column}` → Task: **{self.task_type}**")
        if self.is_imbalanced:
            lines.append(f"  • ⚠️ Class Imbalance: {self.imbalance_ratio:.1f}:1 ratio")
        if self.has_missing_values:
            n_missing = len(self.missing_columns)
            lines.append(f"  • ⚠️ Missing Values: {n_missing} column(s) affected")
        if self.has_outliers:
            lines.append(f"  • ⚠️ Outliers detected in: {', '.join(self.outlier_columns[:5])}")
        if self.is_high_dimensional:
            lines.append(f"  • ⚠️ High Dimensionality: {self.n_cols} features")
        if self.has_multicollinearity:
            lines.append(f"  • ⚠️ Multicollinearity: {len(self.multicollinear_pairs)} correlated pairs")
        if self.has_high_cardinality:
            lines.append(f"  • ⚠️ High Cardinality: {', '.join(self.high_cardinality_columns[:3])}")
        lines.append(f"  • Size Class: **{self.dataset_size_class}** | Domain: **{self.domain_hint}**")
        return "\n".join(lines)


class ContextUnderstandingEngine:
    """
    Analyzes datasets to produce structured context signals.
    These signals drive the Workflow Adaptation Engine.
    """

    CARDINALITY_THRESHOLD = 50
    TEXT_LENGTH_THRESHOLD = 50
    TEXT_UNIQUE_RATIO_THRESHOLD = 0.5
    MISSING_THRESHOLD = 0.01
    IMBALANCE_THRESHOLD = 3.0
    HIGH_DIM_THRESHOLD = 100
    LARGE_DATASET_THRESHOLD = 100_000
    OUTLIER_SIGMA = 3.0
    CORRELATION_THRESHOLD = 0.9

    def analyze(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        user_intent: str = "",
        domain_hint: str = "",
    ) -> ContextSignals:
        """Run full dataset analysis and return context signals."""
        signals = ContextSignals()
        signals.n_rows = len(df)
        signals.n_cols = len(df.columns)

        # Classify columns
        self._classify_columns(df, signals)

        # Target and task detection
        if target_column and target_column in df.columns:
            signals.target_column = target_column
            signals.task_type = self._detect_task_type(df, target_column, user_intent)
            if signals.task_type in ("binary_classification", "multiclass_classification"):
                signals.imbalance_ratio, signals.is_imbalanced = self._check_imbalance(df, target_column)
                signals.class_distribution = df[target_column].value_counts().to_dict()
        elif user_intent:
            signals.task_type = self._infer_task_from_intent(user_intent)

        # Data quality checks
        self._check_missing_values(df, signals)
        self._check_outliers(df, signals)
        self._check_high_cardinality(df, signals)
        self._check_multicollinearity(df, signals)

        # Size classification
        signals.is_high_dimensional = signals.n_cols > self.HIGH_DIM_THRESHOLD
        signals.is_large_dataset = signals.n_rows > self.LARGE_DATASET_THRESHOLD
        signals.dataset_size_class = self._classify_size(df)

        # Domain inference
        signals.domain_hint = domain_hint if domain_hint else self._infer_domain(df, user_intent)

        # Numeric summary
        if signals.numeric_columns:
            signals.numeric_summary = df[signals.numeric_columns].describe().to_dict()

        # Feature types summary
        signals.feature_types_summary = {
            "numeric": len(signals.numeric_columns),
            "categorical": len(signals.categorical_columns),
            "text": len(signals.text_columns),
            "datetime": len(signals.datetime_columns),
            "boolean": len(signals.boolean_columns),
        }

        return signals

    def detect_drift(self, df_old: pd.DataFrame, df_new: pd.DataFrame, num_cols: List[str]) -> Dict[str, Dict]:
        """Detect real data drift using KS-Test for numeric columns."""
        drift_results = {}
        for col in num_cols:
            if col in df_old.columns and col in df_new.columns:
                old_data = df_old[col].dropna()
                new_data = df_new[col].dropna()
                if len(old_data) > 10 and len(new_data) > 10:
                    stat, p_value = stats.ks_2samp(old_data, new_data)
                    is_drift = p_value < 0.05
                    drift_results[col] = {
                        "drift_score": float(stat),
                        "p_value": float(p_value),
                        "drift_detected": bool(is_drift)
                    }
        return drift_results

    def _classify_columns(self, df: pd.DataFrame, signals: ContextSignals):
        """Classify each column by its data type."""
        for col in df.columns:
            dtype = df[col].dtype

            # Boolean
            if dtype == bool or (df[col].nunique() == 2 and set(df[col].dropna().unique()).issubset({0, 1, True, False, "True", "False", "yes", "no", "Yes", "No"})):
                signals.boolean_columns.append(col)
                continue

            # DateTime
            if pd.api.types.is_datetime64_any_dtype(dtype):
                signals.datetime_columns.append(col)
                signals.has_time_column = True
                continue

            # Try parsing as datetime
            if dtype == object:
                try:
                    sample = df[col].dropna().head(20)
                    pd.to_datetime(sample, infer_datetime_format=True)
                    signals.datetime_columns.append(col)
                    signals.has_time_column = True
                    continue
                except (ValueError, TypeError):
                    pass

            # Numeric
            if pd.api.types.is_numeric_dtype(dtype):
                signals.numeric_columns.append(col)
                continue

            # Text vs Categorical
            if dtype == object or pd.api.types.is_string_dtype(dtype):
                avg_len = df[col].dropna().astype(str).str.len().mean()
                unique_ratio = df[col].nunique() / max(len(df), 1)
                if avg_len > self.TEXT_LENGTH_THRESHOLD and unique_ratio > self.TEXT_UNIQUE_RATIO_THRESHOLD:
                    signals.text_columns.append(col)
                    signals.has_text_column = True
                else:
                    signals.categorical_columns.append(col)

    def _detect_task_type(self, df: pd.DataFrame, target: str, intent: str) -> str:
        """Detect ML task type from target column characteristics."""
        target_col = df[target]
        n_unique = target_col.nunique()
        dtype = target_col.dtype

        # Check intent keywords first
        intent_lower = intent.lower()
        if any(kw in intent_lower for kw in ["forecast", "time series", "predict future", "temporal"]):
            return "time_series_forecasting"
        if any(kw in intent_lower for kw in ["cluster", "segment", "group"]):
            return "clustering"
        if any(kw in intent_lower for kw in ["anomaly", "outlier", "fraud", "unusual"]):
            return "anomaly_detection"
        if any(kw in intent_lower for kw in ["sentiment", "text class", "nlp", "language"]):
            return "nlp_classification"

        # Infer from target characteristics
        if pd.api.types.is_numeric_dtype(dtype) and n_unique > 20:
            return "regression"
        elif n_unique == 2:
            return "binary_classification"
        elif n_unique <= 20:
            return "multiclass_classification"
        else:
            return "regression"

    def _infer_task_from_intent(self, intent: str) -> str:
        """Infer task type from user intent string alone."""
        intent_lower = intent.lower()
        task_keywords = {
            "binary_classification": ["classify", "predict class", "yes or no", "churn", "attrition", "fraud"],
            "multiclass_classification": ["categorize", "multi-class", "classify into"],
            "regression": ["predict value", "forecast amount", "estimate price", "regression"],
            "time_series_forecasting": ["forecast", "time series", "future", "trend"],
            "clustering": ["cluster", "segment", "group", "unsupervised"],
            "anomaly_detection": ["anomaly", "outlier", "fraud", "unusual pattern"],
            "nlp_classification": ["sentiment", "text", "nlp", "review"],
        }
        for task, keywords in task_keywords.items():
            if any(kw in intent_lower for kw in keywords):
                return task
        return "unknown"

    def _check_imbalance(self, df: pd.DataFrame, target: str) -> Tuple[float, bool]:
        """Check class imbalance ratio."""
        counts = df[target].value_counts()
        if len(counts) < 2:
            return 1.0, False
        ratio = counts.iloc[0] / counts.iloc[-1]
        return ratio, ratio > self.IMBALANCE_THRESHOLD

    def _check_missing_values(self, df: pd.DataFrame, signals: ContextSignals):
        """Detect columns with missing values."""
        missing = df.isnull().mean()
        signals.missing_columns = {col: float(ratio) for col, ratio in missing.items() if ratio > self.MISSING_THRESHOLD}
        signals.overall_missing_ratio = float(df.isnull().mean().mean())
        signals.has_missing_values = len(signals.missing_columns) > 0

    def _check_outliers(self, df: pd.DataFrame, signals: ContextSignals):
        """Detect numeric columns with significant outliers."""
        outlier_cols = []
        for col in df.select_dtypes(include=[np.number]).columns:
            col_data = df[col].dropna()
            if len(col_data) < 10:
                continue
            z_scores = np.abs(stats.zscore(col_data, nan_policy="omit"))
            outlier_pct = (z_scores > self.OUTLIER_SIGMA).mean()
            if outlier_pct > 0.01:
                outlier_cols.append(col)
        signals.outlier_columns = outlier_cols
        signals.has_outliers = len(outlier_cols) > 0

    def _check_high_cardinality(self, df: pd.DataFrame, signals: ContextSignals):
        """Detect categorical columns with high cardinality."""
        high_card = []
        for col in signals.categorical_columns:
            if df[col].nunique() > self.CARDINALITY_THRESHOLD:
                high_card.append(col)
        signals.high_cardinality_columns = high_card
        signals.has_high_cardinality = len(high_card) > 0

    def _check_multicollinearity(self, df: pd.DataFrame, signals: ContextSignals):
        """Detect pairs of highly correlated numeric features."""
        num_cols = [c for c in signals.numeric_columns if c != signals.target_column]
        if len(num_cols) < 2 or len(num_cols) > 200:
            return

        try:
            corr_matrix = df[num_cols].corr().abs()
            pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    if corr_matrix.iloc[i, j] > self.CORRELATION_THRESHOLD:
                        pairs.append((corr_matrix.columns[i], corr_matrix.columns[j]))
            signals.multicollinear_pairs = pairs[:10]
            signals.has_multicollinearity = len(pairs) > 0
        except Exception:
            pass

    def _classify_size(self, df: pd.DataFrame) -> str:
        """Classify dataset size."""
        n = len(df)
        if n < 1_000:
            return "small"
        elif n < 10_000:
            return "medium"
        elif n < 100_000:
            return "large"
        else:
            return "very_large"

    def _infer_domain(self, df: pd.DataFrame, intent: str) -> str:
        """Infer domain from column names and user intent."""
        all_text = " ".join(df.columns.tolist()).lower() + " " + intent.lower()

        domain_keywords = {
            "manufacturing": ["sensor", "vibration", "temperature", "rpm", "machine", "motor", "pressure", "torque", "maintenance"],
            "healthcare": ["patient", "diagnosis", "treatment", "clinical", "medical", "heart", "blood", "hospital"],
            "finance": ["transaction", "fraud", "account", "credit", "debit", "amount", "balance", "payment"],
            "retail": ["sales", "product", "customer", "revenue", "store", "inventory", "sku", "price"],
            "hr": ["employee", "attrition", "salary", "department", "satisfaction", "performance", "tenure"],
            "energy": ["power", "energy", "consumption", "grid", "solar", "wind", "generation"],
        }

        for domain, keywords in domain_keywords.items():
            matches = sum(1 for kw in keywords if kw in all_text)
            if matches >= 2:
                return domain
        return "general"
