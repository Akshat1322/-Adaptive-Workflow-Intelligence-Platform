"""
AWIP — Adaptive Workflow Intelligence Platform
Pipeline Executor

Converts WorkflowDAG into executable scikit-learn/imblearn pipelines
and trains models on the provided dataset.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    roc_auc_score, mean_squared_error, r2_score, mean_absolute_error,
    classification_report, confusion_matrix, silhouette_score
)
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.preprocessing import StandardScaler, RobustScaler, OrdinalEncoder, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
import warnings

warnings.filterwarnings("ignore")

try:
    from imblearn.pipeline import Pipeline as ImbPipeline
    from imblearn.over_sampling import SMOTE, SMOTENC
    from imblearn.combine import SMOTETomek
    HAS_IMBLEARN = True
except ImportError:
    HAS_IMBLEARN = False

try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from lightgbm import LGBMClassifier, LGBMRegressor
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


class PipelineExecutor:
    """
    Converts a WorkflowDAG into an executable pipeline and runs training + evaluation.
    """

    def __init__(self):
        self.pipeline = None
        self.model = None
        self.label_encoder = None
        self.results = {}
        self.shap_values = None
        self.feature_names = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None

    def execute(
        self,
        df: pd.DataFrame,
        workflow_dag,
        target_column: str,
        signals,
        test_size: float = 0.2,
    ) -> Dict[str, Any]:
        """Execute the full pipeline: build, train, evaluate, explain."""
        results = {"status": "running", "steps_executed": [], "metrics": {}, "errors": []}

        try:
            # Prepare data
            X, y = self._prepare_data(df, target_column, signals)
            results["steps_executed"].append("✅ Data prepared")

            # Split
            from sklearn.model_selection import train_test_split
            stratify = y if signals.task_type in ("binary_classification", "multiclass_classification") else None
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42, stratify=stratify
                )
            except ValueError:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42
                )
            self.X_train, self.X_test = X_train, X_test
            self.y_train, self.y_test = y_train, y_test
            self.feature_names = list(X.columns)
            results["steps_executed"].append(f"✅ Train/Test split ({len(X_train)}/{len(X_test)})")

            # Build pipeline
            pipeline_steps = self._build_pipeline_steps(workflow_dag, signals, X_train)
            results["steps_executed"].append("✅ Pipeline constructed")

            # Train
            if HAS_IMBLEARN and any(s.category == "sampling" for s in workflow_dag.steps):
                self.pipeline = ImbPipeline(pipeline_steps)
            else:
                # Remove sampling steps
                pipeline_steps = [(n, s) for n, s in pipeline_steps
                                  if not (HAS_IMBLEARN and isinstance(s, (SMOTE, SMOTETomek)))]
                self.pipeline = Pipeline(pipeline_steps)

            self.pipeline.fit(X_train, y_train)
            results["steps_executed"].append("✅ Model trained")

            # Evaluate
            metrics = self._evaluate(X_test, y_test, signals.task_type)
            results["metrics"] = metrics
            results["steps_executed"].append("✅ Evaluation complete")

            # Cross-validation
            cv_scores = self._cross_validate(X, y, workflow_dag, signals)
            results["cv_scores"] = cv_scores
            results["steps_executed"].append("✅ Cross-validation complete")

            # Leaderboard generation
            results["leaderboard"] = self._generate_leaderboard(X_train, y_train, X_test, y_test, signals.task_type)
            results["steps_executed"].append("✅ Leaderboard generated")

            # SHAP explanation
            shap_data = self._compute_shap(X_test, workflow_dag, signals)
            if shap_data:
                results["shap_data"] = shap_data
                results["steps_executed"].append("✅ SHAP analysis complete")

            results["status"] = "success"

        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            import traceback
            results["traceback"] = traceback.format_exc()

        self.results = results
        return results

    def _prepare_data(self, df: pd.DataFrame, target: str, signals) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target."""
        X = df.drop(columns=[target])
        y = df[target].copy()

        # Drop datetime columns (they need special handling)
        dt_cols = [c for c in signals.datetime_columns if c in X.columns]
        if dt_cols:
            X = X.drop(columns=dt_cols)

        # Drop text columns for now (need NLP pipeline)
        txt_cols = [c for c in signals.text_columns if c in X.columns]
        if txt_cols:
            X = X.drop(columns=txt_cols)

        # Pre-encode categorical columns so numeric-only transformers (KNNImputer, scalers) work
        cat_cols = X.select_dtypes(include=[object, "category"]).columns.tolist()
        self._cat_encoders = {}
        for col in cat_cols:
            enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
            X[col] = enc.fit_transform(X[[col]])
            self._cat_encoders[col] = enc

        # Encode target if classification
        if signals.task_type in ("binary_classification", "multiclass_classification"):
            if y.dtype == object or y.dtype.name == "category":
                self.label_encoder = LabelEncoder()
                y = pd.Series(self.label_encoder.fit_transform(y), index=y.index)

        return X, y

    def _build_pipeline_steps(self, workflow_dag, signals, X_train) -> list:
        """Convert WorkflowDAG steps into sklearn pipeline steps."""
        steps = []
        model_step = None

        for ws in workflow_dag.steps:
            if ws.category == "model":
                model_step = ws
                continue
            elif ws.category == "explainability":
                continue  # Handled separately

            step = self._create_sklearn_step(ws, signals, X_train)
            if step:
                steps.append(step)

        # Add model last
        if model_step:
            model = self._create_model(model_step, signals)
            if model:
                steps.append(("model", model))
                self.model = model

        return steps

    def _create_sklearn_step(self, ws, signals, X_train):
        """Create a single sklearn pipeline step."""
        name = ws.name.lower().replace(" ", "_")

        if "imputer" in ws.name.lower() or "imput" in ws.name.lower():
            if "knn" in ws.name.lower():
                return (name, KNNImputer(n_neighbors=ws.params.get("n_neighbors", 5)))
            elif "iterative" in ws.name.lower():
                try:
                    from sklearn.experimental import enable_iterative_imputer
                    from sklearn.impute import IterativeImputer
                    return (name, IterativeImputer(max_iter=ws.params.get("max_iter", 10)))
                except ImportError:
                    return (name, SimpleImputer(strategy="median"))
            else:
                return (name, SimpleImputer(strategy="median"))

        elif "ordinal" in ws.name.lower():
            # Categoricals already pre-encoded in _prepare_data
            return None

        elif "target" in ws.name.lower() and "encoder" in ws.name.lower():
            # Categoricals already pre-encoded in _prepare_data
            return None

        elif "robust" in ws.name.lower():
            return (name, RobustScaler())

        elif "standard" in ws.name.lower():
            return (name, StandardScaler())

        elif "pca" in ws.name.lower():
            n_comp = ws.params.get("n_components", 0.95)
            return (name, PCA(n_components=n_comp))

        elif "smote" in ws.name.lower() and HAS_IMBLEARN:
            if "tomek" in ws.name.lower():
                return (name, SMOTETomek(random_state=42))
            else:
                strategy = ws.params.get("sampling_strategy", "auto")
                return (name, SMOTE(sampling_strategy=strategy, random_state=42))

        return None

    def _create_model(self, ws, signals):
        """Create the ML model instance."""
        name = ws.name

        if "ARIMA" in name or "Prophet" in name:
            try:
                from prophet import Prophet
                return Prophet() # In a real scenario we'd wrap this to be sklearn-compatible
            except ImportError:
                return RandomForestRegressor(n_estimators=100, random_state=42)

        if "XGBoost" in name and "Regressor" in name:
            if HAS_XGBOOST:
                return XGBRegressor(**{k: v for k, v in ws.params.items() if v is not None})
            return RandomForestRegressor(n_estimators=200, random_state=42)

        elif "XGBoost" in name:
            if HAS_XGBOOST:
                params = {k: v for k, v in ws.params.items() if v is not None}
                params.setdefault("use_label_encoder", False)
                params.setdefault("eval_metric", "logloss")
                return XGBClassifier(**params)
            return RandomForestClassifier(n_estimators=200, random_state=42)

        elif "LightGBM" in name:
            if HAS_LIGHTGBM:
                params = {k: v for k, v in ws.params.items() if v is not None}
                params["verbose"] = -1
                if signals.task_type == "regression":
                    return LGBMRegressor(**params)
                return LGBMClassifier(**params)
            return RandomForestClassifier(n_estimators=200, random_state=42)

        elif "RandomForest" in name:
            params = {k: v for k, v in ws.params.items() if v is not None}
            if signals.task_type == "regression":
                return RandomForestRegressor(**params)
            return RandomForestClassifier(**params)

        elif "Logistic" in name:
            params = {k: v for k, v in ws.params.items() if v is not None}
            return LogisticRegression(**params)

        elif "Ridge" in name:
            return Ridge(alpha=ws.params.get("alpha", 1.0))

        elif "IsolationForest" in name:
            return IsolationForest(
                n_estimators=ws.params.get("n_estimators", 200),
                contamination=ws.params.get("contamination", 0.05),
                random_state=42,
            )

        # Fallback
        if signals.task_type == "regression":
            return RandomForestRegressor(n_estimators=200, random_state=42)
        return RandomForestClassifier(n_estimators=200, random_state=42)

    def _evaluate(self, X_test, y_test, task_type: str) -> Dict[str, float]:
        """Evaluate the trained pipeline."""
        y_pred = self.pipeline.predict(X_test)
        metrics = {}

        if task_type in ("binary_classification", "multiclass_classification"):
            metrics["accuracy"] = round(accuracy_score(y_test, y_pred), 4)
            avg = "binary" if task_type == "binary_classification" else "weighted"
            metrics["f1_score"] = round(f1_score(y_test, y_pred, average=avg, zero_division=0), 4)
            metrics["precision"] = round(precision_score(y_test, y_pred, average=avg, zero_division=0), 4)
            metrics["recall"] = round(recall_score(y_test, y_pred, average=avg, zero_division=0), 4)
            try:
                if task_type == "binary_classification":
                    y_proba = self.pipeline.predict_proba(X_test)[:, 1]
                    metrics["auc_roc"] = round(roc_auc_score(y_test, y_proba), 4)
                else:
                    y_proba = self.pipeline.predict_proba(X_test)
                    metrics["auc_roc"] = round(roc_auc_score(y_test, y_proba, multi_class="ovr", average="weighted"), 4)
            except Exception:
                pass
            metrics["classification_report"] = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            metrics["confusion_matrix"] = confusion_matrix(y_test, y_pred).tolist()

        elif task_type == "regression":
            metrics["rmse"] = round(np.sqrt(mean_squared_error(y_test, y_pred)), 4)
            metrics["mae"] = round(mean_absolute_error(y_test, y_pred), 4)
            metrics["r2_score"] = round(r2_score(y_test, y_pred), 4)

        return metrics

    def _generate_leaderboard(self, X_train, y_train, X_test, y_test, task_type):
        leaderboard = []
        
        # We need preprocessed data. Since X_train is pre-split, we should use the pipeline without the model.
        # But for simplicity, we'll just impute and scale here quickly.
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import StandardScaler
        
        # If clustering or anomaly detection, we might not have y_train.
        if task_type in ("binary_classification", "multiclass_classification"):
            candidates = [
                ("LogisticRegression", LogisticRegression(max_iter=500)),
                ("RandomForest", RandomForestClassifier(n_estimators=100, random_state=42)),
            ]
            if HAS_XGBOOST: candidates.append(("XGBoost", XGBClassifier(use_label_encoder=False, eval_metric="logloss")))
            if HAS_LIGHTGBM: candidates.append(("LightGBM", LGBMClassifier(verbose=-1)))
            
            # Simple preprocessor
            X_tr = StandardScaler().fit_transform(SimpleImputer(strategy="median").fit_transform(X_train))
            X_te = StandardScaler().fit_transform(SimpleImputer(strategy="median").fit_transform(X_test))
            
            for name, model in candidates:
                try:
                    model.fit(X_tr, y_train)
                    y_pred = model.predict(X_te)
                    if task_type == "binary_classification":
                        score = roc_auc_score(y_test, model.predict_proba(X_te)[:, 1])
                    else:
                        score = f1_score(y_test, y_pred, average="weighted")
                    leaderboard.append({"name": name, "score": score})
                except Exception:
                    pass

        elif task_type == "regression":
            candidates = [
                ("Ridge Regression", Ridge()),
                ("RandomForestRegressor", RandomForestRegressor(n_estimators=100, random_state=42)),
            ]
            if HAS_XGBOOST: candidates.append(("XGBoostRegressor", XGBRegressor()))
            if HAS_LIGHTGBM: candidates.append(("LightGBMRegressor", LGBMRegressor(verbose=-1)))
            
            X_tr = StandardScaler().fit_transform(SimpleImputer(strategy="median").fit_transform(X_train))
            X_te = StandardScaler().fit_transform(SimpleImputer(strategy="median").fit_transform(X_test))
            
            for name, model in candidates:
                try:
                    model.fit(X_tr, y_train)
                    y_pred = model.predict(X_te)
                    score = r2_score(y_test, y_pred)
                    leaderboard.append({"name": name, "score": score})
                except Exception:
                    pass
        
        elif task_type == "clustering":
            # For clustering, we evaluate on X_train (entire dataset)
            X_tr = StandardScaler().fit_transform(SimpleImputer(strategy="median").fit_transform(X_train))
            candidates = [
                ("KMeans", KMeans(n_clusters=3, random_state=42)),
                ("Agglomerative", AgglomerativeClustering(n_clusters=3)),
                ("DBSCAN", DBSCAN())
            ]
            for name, model in candidates:
                try:
                    if name == "DBSCAN":
                        preds = model.fit_predict(X_tr)
                        if len(set(preds)) > 1:
                            score = silhouette_score(X_tr, preds)
                        else:
                            score = -1.0
                    else:
                        model.fit(X_tr)
                        score = silhouette_score(X_tr, model.labels_)
                    leaderboard.append({"name": name, "score": score})
                except Exception:
                    pass

        # Sort leaderboard descending
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        return leaderboard

    def _cross_validate(self, X, y, workflow_dag, signals) -> Dict:
        """Run cross-validation."""
        try:
            model_step = next((s for s in workflow_dag.steps if s.category == "model"), None)
            if not model_step:
                return {}

            model = self._create_model(model_step, signals)
            if model is None:
                return {}

            # Simple preprocessing for CV
            X_clean = X.copy()
            for col in X_clean.select_dtypes(include=[object, "category"]).columns:
                X_clean[col] = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1).fit_transform(X_clean[[col]])
            X_clean = X_clean.fillna(X_clean.median(numeric_only=True))

            if signals.task_type in ("binary_classification", "multiclass_classification"):
                scoring = "f1_weighted"
                cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            else:
                scoring = "neg_root_mean_squared_error"
                cv = KFold(n_splits=5, shuffle=True, random_state=42)

            scores = cross_val_score(model, X_clean, y, cv=cv, scoring=scoring, error_score="raise")
            return {
                "mean": round(float(np.mean(scores)), 4),
                "std": round(float(np.std(scores)), 4),
                "scores": [round(float(s), 4) for s in scores],
                "metric": scoring,
            }
        except Exception as e:
            return {"error": str(e)}

    def _compute_shap(self, X_test, workflow_dag, signals) -> Optional[Dict]:
        """Compute SHAP values for model explainability."""
        if not HAS_SHAP:
            return None

        try:
            # Get the model from the pipeline
            model = self.pipeline.named_steps.get("model", None)
            if model is None:
                return None

            # Transform X_test through preprocessing steps
            X_transformed = X_test.copy()
            for name, step in self.pipeline.named_steps.items():
                if name == "model":
                    break
                try:
                    X_transformed = pd.DataFrame(
                        step.transform(X_transformed),
                        columns=X_transformed.columns if hasattr(X_transformed, 'columns') else None
                    )
                except Exception:
                    X_transformed = step.transform(X_transformed)

            # Compute SHAP
            if hasattr(model, "feature_importances_"):
                explainer = shap.TreeExplainer(model)
                sample_size = min(100, len(X_transformed))
                if isinstance(X_transformed, pd.DataFrame):
                    X_sample = X_transformed.iloc[:sample_size]
                else:
                    X_sample = X_transformed[:sample_size]

                shap_vals = explainer.shap_values(X_sample)

                # Handle multi-output
                if isinstance(shap_vals, list):
                    shap_vals = shap_vals[1] if len(shap_vals) > 1 else shap_vals[0]

                feature_names = self.feature_names[:shap_vals.shape[1]] if self.feature_names else [f"Feature {i}" for i in range(shap_vals.shape[1])]

                # Get top features
                importance = np.abs(shap_vals).mean(axis=0)
                top_indices = np.argsort(importance)[::-1][:15]
                top_features = [(feature_names[i] if i < len(feature_names) else f"Feature {i}",
                                 float(importance[i])) for i in top_indices]

                return {
                    "top_features": top_features,
                    "method": "TreeExplainer",
                    "n_samples": sample_size,
                }
            else:
                # Feature importance fallback
                if hasattr(model, "coef_"):
                    importance = np.abs(model.coef_).flatten()
                    feature_names = self.feature_names[:len(importance)]
                    top_indices = np.argsort(importance)[::-1][:15]
                    top_features = [(feature_names[i], float(importance[i])) for i in top_indices]
                    return {"top_features": top_features, "method": "Coefficients"}

        except Exception as e:
            return {"error": str(e)}

        return None

    def get_pipeline_code(self, workflow_dag) -> str:
        """Generate reproducible Python code for the pipeline."""
        imports = [
            "import pandas as pd",
            "import numpy as np",
            "from sklearn.model_selection import train_test_split",
        ]
        steps_code = []

        for ws in workflow_dag.steps:
            if ws.category == "explainability":
                continue

            if "KNNImputer" in ws.name:
                imports.append("from sklearn.impute import KNNImputer")
                steps_code.append(f"    ('imputer', KNNImputer(n_neighbors={ws.params.get('n_neighbors', 5)}))")
            elif "IterativeImputer" in ws.name:
                imports.append("from sklearn.experimental import enable_iterative_imputer")
                imports.append("from sklearn.impute import IterativeImputer")
                steps_code.append(f"    ('imputer', IterativeImputer(max_iter={ws.params.get('max_iter', 10)}))")
            elif "OrdinalEncoder" in ws.name:
                imports.append("from sklearn.preprocessing import OrdinalEncoder")
                steps_code.append("    ('encoder', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))")
            elif "TargetEncoder" in ws.name:
                imports.append("from category_encoders import TargetEncoder")
                steps_code.append(f"    ('encoder', TargetEncoder(smoothing={ws.params.get('smoothing', 0.3)}))")
            elif "RobustScaler" in ws.name:
                imports.append("from sklearn.preprocessing import RobustScaler")
                steps_code.append("    ('scaler', RobustScaler())")
            elif "StandardScaler" in ws.name:
                imports.append("from sklearn.preprocessing import StandardScaler")
                steps_code.append("    ('scaler', StandardScaler())")
            elif "PCA" in ws.name:
                imports.append("from sklearn.decomposition import PCA")
                steps_code.append(f"    ('pca', PCA(n_components={ws.params.get('n_components', 0.95)}))")
            elif "SMOTE" in ws.name and "Tomek" in ws.name:
                imports.append("from imblearn.combine import SMOTETomek")
                steps_code.append("    ('sampler', SMOTETomek(random_state=42))")
            elif "SMOTE" in ws.name:
                imports.append("from imblearn.over_sampling import SMOTE")
                steps_code.append(f"    ('sampler', SMOTE(sampling_strategy='{ws.params.get('sampling_strategy', 'auto')}', random_state=42))")
            elif "XGBoost" in ws.name and "Regressor" in ws.name:
                imports.append("from xgboost import XGBRegressor")
                params_str = ", ".join(f"{k}={repr(v)}" for k, v in ws.params.items() if v is not None)
                steps_code.append(f"    ('model', XGBRegressor({params_str}))")
            elif "XGBoost" in ws.name:
                imports.append("from xgboost import XGBClassifier")
                params_str = ", ".join(f"{k}={repr(v)}" for k, v in ws.params.items() if v is not None)
                steps_code.append(f"    ('model', XGBClassifier({params_str}))")
            elif "LightGBM" in ws.name:
                imports.append("from lightgbm import LGBMClassifier")
                params_str = ", ".join(f"{k}={repr(v)}" for k, v in ws.params.items() if v is not None)
                steps_code.append(f"    ('model', LGBMClassifier({params_str}, verbose=-1))")
            elif "RandomForest" in ws.name:
                imports.append("from sklearn.ensemble import RandomForestClassifier")
                params_str = ", ".join(f"{k}={repr(v)}" for k, v in ws.params.items() if v is not None)
                steps_code.append(f"    ('model', RandomForestClassifier({params_str}))")
            elif "Logistic" in ws.name:
                imports.append("from sklearn.linear_model import LogisticRegression")
                params_str = ", ".join(f"{k}={repr(v)}" for k, v in ws.params.items() if v is not None)
                steps_code.append(f"    ('model', LogisticRegression({params_str}))")
            elif "Ridge" in ws.name:
                imports.append("from sklearn.linear_model import Ridge")
                steps_code.append(f"    ('model', Ridge(alpha={ws.params.get('alpha', 1.0)}))")

        # Determine pipeline type
        has_sampling = any("sampler" in s for s in steps_code)
        if has_sampling:
            imports.append("from imblearn.pipeline import Pipeline")
        else:
            imports.append("from sklearn.pipeline import Pipeline")

        # Build final code
        unique_imports = list(dict.fromkeys(imports))  # preserve order, remove dupes
        code = "\n".join(unique_imports) + "\n\n"
        code += "# Auto-generated by AWIP — Adaptive Workflow Intelligence Platform\n"
        code += "pipeline = Pipeline([\n"
        code += ",\n".join(steps_code)
        code += "\n])\n\n"
        code += "# Usage:\n"
        code += "# pipeline.fit(X_train, y_train)\n"
        code += "# predictions = pipeline.predict(X_test)\n"

        return code
