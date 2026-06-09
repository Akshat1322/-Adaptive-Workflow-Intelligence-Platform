import requests
import json

class LLMEngine:
    """Interface to local Ollama server.
    
    LLM is explicitly OPTIONAL. The system works perfectly without it using
    intelligent rule-based explanations. When Ollama is available, it adds
    depth and natural language richness — but it is never required.
    """
    
    _ollama_available: bool | None = None  # cached health check result

    def __init__(self, model_name="llama3", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    @classmethod
    def check_available(cls) -> bool:
        """Check if Ollama is reachable. Result is cached for the process lifetime."""
        if cls._ollama_available is not None:
            return cls._ollama_available
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=3)
            cls._ollama_available = resp.status_code == 200
        except Exception:
            cls._ollama_available = False
        return cls._ollama_available
    
    @classmethod
    def reset_availability(cls):
        """Force re-check on next call (useful if Ollama was started after the server)."""
        cls._ollama_available = None

    def generate(self, prompt, system="You are an AI data science assistant.", max_tokens=256):
        # Skip the HTTP call entirely if Ollama is known to be unreachable
        if not LLMEngine.check_available():
            return ""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.3
                    }
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                return ""
        except Exception:
            # Mark as unavailable so future calls skip immediately
            LLMEngine._ollama_available = False
            return ""

    def reason_about_workflow(self, signals, steps, user_level):
        system_prompt = (
            f"You are an expert Data Scientist explaining pipeline decisions to a {user_level} user. "
            "Explain WHY these preprocessing steps and model were chosen based on the dataset signals. "
            "Keep it concise, factual, and insightful."
        )
        
        steps_desc = " → ".join([s.name for s in steps])
        prompt = (
            f"Dataset Signals:\n"
            f"- Task: {signals.task_type}\n"
            f"- Rows: {signals.n_rows}\n"
            f"- Missing values: {signals.has_missing_values}\n"
            f"- Imbalanced: {signals.is_imbalanced} (ratio {signals.imbalance_ratio:.1f})\n"
            f"- Outliers: {signals.has_outliers}\n"
            f"- High Cardinality Categoricals: {signals.has_high_cardinality}\n"
            f"- High Dimensionality: {signals.is_high_dimensional}\n"
            f"\n"
            f"Selected Pipeline: {steps_desc}\n\n"
            f"Provide a natural language reasoning for this workflow design tailored to a {user_level}."
        )
        
        result = self.generate(prompt, system_prompt, max_tokens=300)
        if result:
            return result
        
        # Excellent standalone fallback — no generic "[Fallback: ...]" messages
        return self._rule_based_workflow_reasoning(signals, steps)

    def _rule_based_workflow_reasoning(self, signals, steps):
        """High-quality rule-based explanation that works perfectly without LLM."""
        parts = []
        parts.append(f"This is a {signals.task_type.replace('_', ' ')} problem with {signals.n_rows:,} samples and {signals.n_cols} features.")
        
        if signals.has_missing_values:
            max_miss = max(signals.missing_columns.values()) if signals.missing_columns else 0
            if max_miss > 0.3:
                parts.append(f"Heavy missing data ({max_miss:.0%} in the worst column) requires IterativeImputer — it models each feature as a function of the others for more accurate imputation than simple mean/median.")
            else:
                parts.append(f"Moderate missing data detected. KNNImputer was selected because it preserves local data structure by using nearest neighbors for imputation.")
        
        if signals.has_outliers:
            parts.append(f"Outliers detected in {len(signals.outlier_columns)} columns. RobustScaler was chosen because it uses median and IQR instead of mean/std, making it resistant to extreme values.")
        elif any(s.name in ("StandardScaler",) for s in steps):
            parts.append("No significant outliers detected, so StandardScaler (z-score normalization) is appropriate.")
        
        if signals.is_imbalanced:
            parts.append(f"Class imbalance ({signals.imbalance_ratio:.1f}:1 ratio) would cause the model to predict only the majority class. SMOTE generates synthetic minority samples to balance training.")
        
        if signals.has_high_cardinality:
            parts.append("High-cardinality categorical features would create thousands of one-hot columns. TargetEncoder maps categories to their mean target value instead — much more memory-efficient.")
        
        if signals.is_high_dimensional:
            parts.append("High dimensionality increases overfitting risk. PCA reduces features while retaining 95% of explained variance.")
        
        model_step = next((s for s in steps if s.category == "model"), None)
        if model_step:
            model_name = model_step.name.lower()
            if "xgb" in model_name:
                parts.append("XGBoost was selected for its ability to capture complex non-linear feature interactions and its built-in regularization against overfitting.")
            elif "lightgbm" in model_name:
                parts.append("LightGBM was selected for its speed on larger datasets and histogram-based splitting that handles high-cardinality features efficiently.")
            elif "randomforest" in model_name:
                parts.append("Random Forest was selected for its stability — it averages many decision trees, reducing variance and providing robust predictions without extensive tuning.")
            elif "ridge" in model_name or "linear" in model_name:
                parts.append("A linear model was selected because the dataset characteristics favor interpretability and the feature relationships appear approximately linear.")
        
        return " ".join(parts)

    def chat(self, query, workflow, signals, results, user_level):
        system_prompt = (
            f"You are the AWIP Conversational AI, a data science orchestration assistant. "
            f"You are talking to a {user_level} user. Answer their questions based ONLY on the provided context."
        )
        
        steps_desc = " → ".join([s.name for s in workflow.steps]) if workflow else "None"
        best_metric = ""
        if results and results.get("metrics"):
             best_metric = str(results["metrics"])
             
        prompt = (
            f"Context:\n"
            f"Dataset: {signals.n_rows} rows, {signals.n_cols} columns. Task: {signals.task_type}\n"
            f"Workflow: {steps_desc}\n"
            f"Results: {best_metric}\n\n"
            f"User Question: {query}\n\n"
            f"Answer concisely and explain the reasoning behind the system's decisions."
        )
        
        result = self.generate(prompt, system_prompt, max_tokens=300)
        if result:
            return result
        
        # Rule-based chat fallback
        return self._rule_based_chat_response(query, workflow, signals, results)
    
    def _rule_based_chat_response(self, query, workflow, signals, results):
        """Intelligent chat response without LLM."""
        q = query.lower()
        
        if "why" in q and "model" in q:
            model_step = next((s for s in (workflow.steps if workflow else []) if s.category == "model"), None)
            if model_step:
                return f"The system selected {model_step.name} because: {model_step.reason}"
            return "No model has been trained yet. Run the orchestration pipeline first."
        
        if "accuracy" in q or "score" in q or "performance" in q:
            if results and results.get("metrics"):
                metrics = results["metrics"]
                parts = [f"{k.replace('_', ' ').title()}: {v:.4f}" for k, v in metrics.items() 
                        if isinstance(v, (int, float)) and k not in ("confusion_matrix",)]
                return "Current model performance:\n" + "\n".join(f"• {p}" for p in parts[:6])
            return "No results available yet. Upload a dataset and run the pipeline."
        
        if "feature" in q:
            shap_data = results.get("shap_data", {}) if results else {}
            top_features = shap_data.get("top_features", [])
            if top_features:
                lines = ["Top features by SHAP importance:"]
                for name, val in top_features[:5]:
                    lines.append(f"• {name}: {val:.4f}")
                return "\n".join(lines)
            return "Feature importance data is not available yet."
        
        if "workflow" in q or "pipeline" in q or "steps" in q:
            if workflow and workflow.steps:
                desc = " → ".join(s.name for s in workflow.steps)
                return f"Current pipeline: {desc}\n\nEach step was selected based on your dataset's statistical characteristics."
            return "No workflow has been generated yet."
        
        return (
            f"I'm the AWIP assistant. Your dataset has {signals.n_rows if signals else '?'} rows. "
            f"Ask me about model performance, feature importance, pipeline decisions, or data quality."
        )

    def chat_with_context(self, query, workflow, signals, results, 
                          knowledge_base=None, agent_messages=None, user_level="intermediate"):
        """Enhanced chat with full multi-agent context including Knowledge Base."""
        
        # If no signals available, return a simple response
        if signals is None:
            return "No dataset has been analyzed yet. Please upload a CSV first."
        
        system_prompt = (
            f"You are the AWIP AI Data Science Team Lead, an expert orchestration assistant that helps users "
            f"understand their data, model results, and the reasoning of your specialized agents. "
            f"You are speaking to a {user_level} user. Be specific, reference actual "
            f"features and numbers. If you reference past learnings, mention the Knowledge Base."
        )
        
        steps_desc = " → ".join([s.name for s in workflow.steps]) if workflow else "None"
        best_metric = ""
        if results and results.get("metrics"):
            best_metric = str({k: v for k, v in results["metrics"].items() 
                            if k not in ("classification_report", "confusion_matrix")})

        # Build context sections
        context_parts = [
            f"Current Dataset: {signals.n_rows} rows, {signals.n_cols} columns. Task: {signals.task_type}",
            f"Domain: {signals.domain_hint}",
            f"Workflow: {steps_desc}",
            f"Results: {best_metric}",
        ]

        # Add SHAP context
        shap_data = results.get("shap_data", {}) if results else {}
        top_features = shap_data.get("top_features", [])
        if top_features:
            top_str = ", ".join(f"{name} ({val:.4f})" for name, val in top_features[:5])
            context_parts.append(f"Top SHAP Features: {top_str}")

        # Add agent message context
        if agent_messages:
            msg_lines = []
            for msg in agent_messages[-5:]:
                msg_lines.append(f"  {msg.sender}: {msg.content}")
            if msg_lines:
                context_parts.append("Recent Agent Activity:\n" + "\n".join(msg_lines))

        # Add knowledge base context
        if knowledge_base:
            exps = knowledge_base.get_experiments()
            if exps:
                kb_lines = []
                for exp in exps[:3]:
                    kb_lines.append(
                        f"  Dataset: {exp['dataset_name']} | "
                        f"Winner: {exp['winner_model']} | Score: {exp['score']:.4f}"
                    )
                if kb_lines:
                    context_parts.append("Knowledge Base Learnings:\n" + "\n".join(kb_lines))

        prompt = (
            f"Context:\n" + "\n".join(context_parts) + 
            f"\n\nUser Question: {query}\n\n"
            f"Answer as the AI Team Lead. Be specific, insightful, and proactive. "
            f"If you can suggest a follow-up action based on agent findings, do so."
        )
        
        result = self.generate(prompt, system_prompt, max_tokens=400)
        if result:
            return result
        
        # High-quality fallback
        return self._rule_based_chat_response(query, workflow, signals, results)

    def generate_orchestrator_reasoning(self, signals, user_level="intermediate"):
        """Generate LLM-powered orchestrator reasoning for all signals at once."""
        system_prompt = (
            "You are an expert AI Data Scientist. Analyze the dataset signals and explain "
            "your reasoning for the preprocessing and modeling decisions you would make. "
            f"Explain to a {user_level} user. Be concise but thorough."
        )
        
        signal_parts = [
            f"- Task: {signals.task_type}",
            f"- Size: {signals.n_rows:,} rows × {signals.n_cols} columns",
            f"- Missing values: {signals.has_missing_values} ({signals.overall_missing_ratio:.1%} overall)",
            f"- Imbalanced: {signals.is_imbalanced} (ratio {signals.imbalance_ratio:.1f}:1)",
            f"- Outliers: {signals.has_outliers} ({len(signals.outlier_columns)} columns)",
            f"- High cardinality: {signals.has_high_cardinality}",
            f"- High dimensionality: {signals.is_high_dimensional}",
            f"- Multicollinearity: {signals.has_multicollinearity}",
            f"- Domain: {signals.domain_hint}",
        ]
        
        prompt = (
            f"Dataset Signals:\n" + "\n".join(signal_parts) +
            f"\n\nFor each detected issue, explain:\n"
            f"1. What you observed\n"
            f"2. What action you recommend\n"
            f"3. Why this action is the best choice\n\n"
            f"Keep each explanation to 1-2 sentences."
        )
        
        result = self.generate(prompt, system_prompt, max_tokens=500)
        if result:
            return result
        
        # Fallback: use the workflow reasoning helper with a dummy step list
        return "Dataset analysis complete. The pipeline has been configured based on the detected statistical characteristics."
