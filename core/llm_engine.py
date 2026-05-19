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
