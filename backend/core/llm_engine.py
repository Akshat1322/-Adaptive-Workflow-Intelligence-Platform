import requests
import json

class LLMEngine:
    def __init__(self, model_name="llama3", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def generate(self, prompt, system="You are an AI data science assistant.", max_tokens=256):
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
                return f"[LLM Error: {response.status_code}]"
        except Exception as e:
            # Fallback for when Ollama is not running
            return f"[Fallback: Local LLM unreachable. Run `ollama run {self.model_name}`]"

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
        
        return self.generate(prompt, system_prompt, max_tokens=300)

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
        return self.generate(prompt, system_prompt, max_tokens=300)

    def chat_with_context(self, query, workflow, signals, results, 
                          knowledge_base=None, agent_messages=None, user_level="intermediate"):
        """Enhanced chat with full multi-agent context including Knowledge Base."""
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
            for msg in agent_messages[-5:]:  # Get last 5 messages
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
        return self.generate(prompt, system_prompt, max_tokens=400)

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
        
        return self.generate(prompt, system_prompt, max_tokens=500)
