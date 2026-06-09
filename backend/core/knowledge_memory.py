"""
AWIP — AI Data Science Team
Knowledge Base

Replaces the old ExperimentMemory. Converts previous experiments
into reusable intelligence. Stores dataset patterns, successful
workflows, model performance, and domain knowledge.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

class KnowledgeBase:
    """Persistent storage for AI Data Science Team knowledge."""
    
    def __init__(self, memory_file: str = "knowledge_base.json"):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(backend_dir)
        self.memory_path = os.path.join(project_root, memory_file)
        self.knowledge = self._load_knowledge()
        
        if CHROMA_AVAILABLE:
            self.chroma_client = chromadb.PersistentClient(path=os.path.join(backend_dir, "chroma_db"))
            self.collection = self.chroma_client.get_or_create_collection(name="awip_knowledge")
        else:
            self.chroma_client = None
            self.collection = None

    def _load_knowledge(self) -> Dict[str, Any]:
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"experiments": [], "domain_patterns": {}, "successful_models": {}}

    def _save_knowledge(self):
        try:
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge, f, indent=2)
        except Exception as e:
            print(f"Error saving knowledge: {e}")

    def add_experiment(
        self,
        dataset_name: str,
        task_type: str,
        domain: str,
        winner_model: str,
        score: float,
        features_added: int,
        key_issues: List[str]
    ):
        """Save a new experiment and update aggregate knowledge."""
        exp_record = {
            "id": f"EXP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "dataset_name": dataset_name,
            "task_type": task_type,
            "domain": domain,
            "winner_model": winner_model,
            "score": score,
            "features_added": features_added,
            "key_issues": key_issues
        }
        self.knowledge["experiments"].append(exp_record)
        
        # Update successful models
        if task_type not in self.knowledge["successful_models"]:
            self.knowledge["successful_models"][task_type] = {}
        
        if winner_model not in self.knowledge["successful_models"][task_type]:
            self.knowledge["successful_models"][task_type][winner_model] = {"count": 0, "avg_score": 0.0}
            
        stats = self.knowledge["successful_models"][task_type][winner_model]
        total_score = stats["avg_score"] * stats["count"]
        stats["count"] += 1
        stats["avg_score"] = (total_score + score) / stats["count"]
        
        # Update domain patterns
        if domain != "auto-detect":
            if domain not in self.knowledge["domain_patterns"]:
                self.knowledge["domain_patterns"][domain] = []
            self.knowledge["domain_patterns"][domain].append({
                "dataset": dataset_name,
                "winner": winner_model,
                "score": score
            })
            
        self._save_knowledge()
        
        # Add to ChromaDB
        if self.collection:
            doc_content = f"Dataset: {dataset_name}. Task: {task_type}. Domain: {domain}. Best Model: {winner_model}. Score: {score:.4f}. Features added: {features_added}. Issues: {', '.join(key_issues)}"
            self.collection.add(
                documents=[doc_content],
                metadatas=[{"task": task_type, "domain": domain, "model": winner_model}],
                ids=[exp_record["id"]]
            )
            
    def semantic_search(self, query: str, n_results: int = 3) -> List[str]:
        """Query the vector database for relevant past knowledge."""
        structured = self.search_experiments(query, n_results)
        return [r.get("summary", "") for r in structured if r.get("summary")]

    def search_experiments(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Semantic search returning structured experiment cards for the UI."""
        experiments = self.knowledge.get("experiments", [])
        if not query.strip():
            return [self._experiment_to_card(exp, 100) for exp in reversed(experiments[-n_results:])]

        if not self.collection or self.collection.count() == 0:
            return self._fallback_text_search(query, experiments, n_results)

        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count())
        )
        if not results.get("documents") or not results["documents"][0]:
            return self._fallback_text_search(query, experiments, n_results)

        cards = []
        for i, doc in enumerate(results["documents"][0]):
            exp_id = results["ids"][0][i] if results.get("ids") else None
            distance = results["distances"][0][i] if results.get("distances") else 0.5
            match_pct = max(0, min(100, int((1 - distance) * 100)))
            exp = next((e for e in experiments if e.get("id") == exp_id), None)
            if exp:
                cards.append(self._experiment_to_card(exp, match_pct))
            else:
                cards.append({
                    "id": exp_id or f"search_{i}",
                    "queryMatch": f"{match_pct}%",
                    "dataset": "Past Experiment",
                    "domain": results["metadatas"][0][i].get("domain", "general") if results.get("metadatas") else "general",
                    "workflow": results["metadatas"][0][i].get("model", "Unknown pipeline") if results.get("metadatas") else "Unknown pipeline",
                    "performance": doc.split("Score: ")[1].split(".")[0] + "." if "Score: " in doc else "N/A",
                    "insight": doc,
                    "summary": doc,
                })
        return cards

    def _fallback_text_search(self, query: str, experiments: List[Dict], n_results: int) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        scored = []
        for exp in experiments:
            haystack = " ".join([
                exp.get("dataset_name", ""),
                exp.get("task_type", ""),
                exp.get("domain", ""),
                exp.get("winner_model", ""),
                " ".join(exp.get("key_issues", [])),
            ]).lower()
            if query_lower in haystack:
                scored.append((100, exp))
            elif any(word in haystack for word in query_lower.split() if len(word) > 2):
                scored.append((65, exp))
        scored.sort(key=lambda x: x[0], reverse=True)
        if not scored:
            return [self._experiment_to_card(exp, 50) for exp in reversed(experiments[-n_results:])]
        return [self._experiment_to_card(exp, score) for score, exp in scored[:n_results]]

    def _experiment_to_card(self, exp: Dict[str, Any], match_pct: int) -> Dict[str, Any]:
        issues = exp.get("key_issues") or []
        insight = (
            f"Winner model {exp.get('winner_model', 'Unknown')} achieved "
            f"{exp.get('score', 0):.4f} on {exp.get('task_type', 'unknown').replace('_', ' ')}."
        )
        if issues:
            insight += f" Key issues: {', '.join(issues)}."
        summary = (
            f"Dataset: {exp.get('dataset_name')}. Task: {exp.get('task_type')}. "
            f"Domain: {exp.get('domain')}. Best Model: {exp.get('winner_model')}. "
            f"Score: {exp.get('score', 0):.4f}."
        )
        return {
            "id": exp.get("id"),
            "queryMatch": f"{match_pct}%",
            "dataset": exp.get("dataset_name", "Unknown"),
            "domain": str(exp.get("domain", "general")).replace("_", " ").title(),
            "workflow": exp.get("winner_model", "Unknown"),
            "performance": f"Score: {exp.get('score', 0):.4f}",
            "insight": insight,
            "summary": summary,
        }

    def get_experiments(self) -> List[Dict]:
        return list(reversed(self.knowledge.get("experiments", [])))
        
    def get_experiment_count(self) -> int:
        return len(self.knowledge.get("experiments", []))
        
    def get_domain_knowledge(self, domain: str) -> List[Dict]:
        return self.knowledge.get("domain_patterns", {}).get(domain, [])
        
    def get_best_model_for_task(self, task_type: str) -> str:
        models = self.knowledge.get("successful_models", {}).get(task_type, {})
        if not models:
            return "Unknown"
        # Sort by avg score
        sorted_models = sorted(models.items(), key=lambda x: x[1]["avg_score"], reverse=True)
        return sorted_models[0][0]
