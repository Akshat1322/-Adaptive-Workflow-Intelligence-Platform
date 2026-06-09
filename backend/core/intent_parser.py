"""
AWIP — AI Data Science Workspace
Intent Parser

Maps natural language commands from the user to specific workspace actions.
Intents:
- NAVIGATE: "Go to reports", "Show experiments"
- EXPLAIN: "Why did you choose XGBoost?", "Explain this feature"
- MODIFY: "Improve recall", "Drop the 'age' column"
- GENERATE_REPORT: "Create an executive summary"
- QUERY_KNOWLEDGE: "What usually works for HR data?"
- EXECUTE: "Deploy model", "Analyze drift"
- GENERAL: Conversational fallback
"""

import json
from .llm_engine import LLMEngine

class IntentParser:
    def __init__(self):
        self.llm = LLMEngine()
        self.intents = [
            "NAVIGATE", "EXPLAIN", "MODIFY", 
            "GENERATE_REPORT", "QUERY_KNOWLEDGE", "EXECUTE", "GENERAL"
        ]
        
    def parse_intent(self, query: str) -> dict:
        """
        Parses the user query and returns a dictionary with 'intent' and optional 'entities'.
        """
        system_prompt = (
            "You are the AWIP Command Router. Analyze the user's natural language command "
            "and map it to one of the following exact intent strings:\n"
            "NAVIGATE: For navigating the workspace (e.g., 'show experiments', 'go to reports', 'open knowledge base').\n"
            "EXPLAIN: For asking why something happened or how a model works.\n"
            "MODIFY: For requesting changes to the pipeline (e.g., 'improve recall', 'drop column').\n"
            "GENERATE_REPORT: For requesting a report (e.g., 'generate executive summary').\n"
            "QUERY_KNOWLEDGE: For asking about past experiments or historical domain knowledge.\n"
            "EXECUTE: For autonomous system actions (e.g., 'deploy model', 'analyze drift', 'run experiment').\n"
            "GENERAL: For casual chat or if no other intent fits.\n\n"
            "Respond ONLY with a valid JSON object in the format: {\"intent\": \"INTENT_NAME\", \"target\": \"optional context\"}."
        )
        
        prompt = f"User Command: {query}"
        
        try:
            response = self.llm.generate(prompt, system=system_prompt, max_tokens=100)
            
            # Very basic extraction if the LLM wraps it in markdown blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].strip()
                
            parsed = json.loads(response)
            
            # Validate intent
            if parsed.get("intent") not in self.intents:
                parsed["intent"] = "GENERAL"
                
            return parsed
        except Exception as e:
            # Fallback heuristic logic if LLM offline or JSON fails
            return self._heuristic_fallback(query)
            
    def _heuristic_fallback(self, query: str) -> dict:
        q = query.lower()
        if any(word in q for word in ["go to", "show me", "open", "navigate", "view"]):
            return {"intent": "NAVIGATE", "target": query}
        elif "report" in q or "summary" in q:
            return {"intent": "GENERATE_REPORT", "target": query}
        elif "explain" in q or "why" in q or "how" in q:
            return {"intent": "EXPLAIN", "target": query}
        elif "improve" in q or "reduce" in q or "drop" in q or "change" in q or "add" in q:
            return {"intent": "MODIFY", "target": query}
        elif "deploy" in q or "run" in q or "analyze drift" in q:
            return {"intent": "EXECUTE", "target": query}
        elif "history" in q or "past" in q or "usually" in q or "before" in q:
            return {"intent": "QUERY_KNOWLEDGE", "target": query}
        
        return {"intent": "GENERAL", "target": query}
