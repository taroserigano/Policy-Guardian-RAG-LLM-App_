"""
Enhanced evaluation script comparing base, v1, and v2 fine-tuned models.
Tests on policy/legal specific queries.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from pathlib import Path
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm


# Policy-specific test queries categorized by domain
POLICY_TEST_CASES = {
    "remote_work": {
        "queries": [
            "What is the work from home policy?",
            "Can employees work remotely?",
            "WFH guidelines",
            "Remote work requirements",
            "How do I request to telecommute?",
        ],
        "expected_keywords": ["remote", "home", "wfh", "telecommute", "virtual"]
    },
    "leave_policy": {
        "queries": [
            "How many vacation days do I get?",
            "PTO policy",
            "What is the sick leave policy?",
            "Annual leave entitlement",
            "Time off request process",
        ],
        "expected_keywords": ["leave", "vacation", "pto", "sick", "time off", "days"]
    },
    "confidentiality": {
        "queries": [
            "NDA requirements",
            "What is considered confidential?",
            "Non-disclosure agreement",
            "Proprietary information handling",
            "How to handle sensitive data?",
        ],
        "expected_keywords": ["confidential", "nda", "disclosure", "proprietary", "sensitive"]
    },
    "data_privacy": {
        "queries": [
            "Data protection policy",
            "Personal information handling",
            "Privacy requirements",
            "How is employee data protected?",
            "Data security measures",
        ],
        "expected_keywords": ["data", "privacy", "personal", "protection", "security"]
    },
    "security": {
        "queries": [
            "Information security policy",
            "Password requirements",
            "Security breach reporting",
            "Device security guidelines",
            "How to report a security incident?",
        ],
        "expected_keywords": ["security", "password", "breach", "incident", "device"]
    }
}


class EnhancedEvaluator:
    """Compare multiple embedding models on policy retrieval."""
    
    def __init__(self):
        self.models = {}
        self.documents = []
        self.doc_names = []
    
    def load_model(self, name: str, path: str):
        """Load a model for comparison."""
        print(f"Loading model '{name}' from {path}...")
        try:
            self.models[name] = SentenceTransformer(path)
            print(f"  ✓ Loaded successfully")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    def load_documents(self, docs_dir: str):
        """Load test documents."""
        docs_path = Path(docs_dir)
        for file_path in docs_path.glob("*.txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Chunk the document
                words = content.split()
                for i in range(0, len(words), 300):
                    chunk = ' '.join(words[i:i+400])
                    if len(chunk.split()) >= 50:
                        self.documents.append(chunk)
                        self.doc_names.append(file_path.name)
        
        print(f"Loaded {len(self.documents)} document chunks")
    
    def evaluate_retrieval(self, model_name: str, queries: List[str], top_k: int = 5) -> Dict:
        """Evaluate retrieval quality for a model."""
        model = self.models[model_name]
        
        # Encode documents
        doc_embeddings = model.encode(self.documents, show_progress_bar=False)
        
        results = []
        for query in queries:
            query_embedding = model.encode(query)
            
            # Compute similarities
            similarities = util.cos_sim(query_embedding, doc_embeddings)[0]
            top_indices = similarities.argsort(descending=True)[:top_k]
            
            top_scores = [similarities[i].item() for i in top_indices]
            top_docs = [self.doc_names[i] for i in top_indices]
            
            results.append({
                "query": query,
                "top_scores": top_scores,
                "top_docs": top_docs,
                "mean_score": np.mean(top_scores),
                "max_score": max(top_scores)
            })
        
        return {
            "results": results,
            "mean_top1": np.mean([r["max_score"] for r in results]),
            "mean_top5": np.mean([r["mean_score"] for r in results])
        }
    
    def run_domain_evaluation(self):
        """Run evaluation across all policy domains."""
        print("\n" + "=" * 70)
        print("Domain-Specific Retrieval Evaluation")
        print("=" * 70)
        
        all_results = {}
        
        for domain, test_case in POLICY_TEST_CASES.items():
            print(f"\n📂 Domain: {domain.upper()}")
            print("-" * 50)
            
            domain_results = {}
            for model_name in self.models:
                eval_result = self.evaluate_retrieval(model_name, test_case["queries"])
                domain_results[model_name] = eval_result
                
                print(f"  {model_name:20} | Top-1: {eval_result['mean_top1']:.4f} | Top-5: {eval_result['mean_top5']:.4f}")
            
            all_results[domain] = domain_results
        
        return all_results
    
    def compute_summary(self, all_results: Dict):
        """Compute overall summary statistics."""
        print("\n" + "=" * 70)
        print("OVERALL SUMMARY")
        print("=" * 70)
        
        model_scores = {name: {"top1": [], "top5": []} for name in self.models}
        
        for domain, domain_results in all_results.items():
            for model_name, result in domain_results.items():
                model_scores[model_name]["top1"].append(result["mean_top1"])
                model_scores[model_name]["top5"].append(result["mean_top5"])
        
        print(f"\n{'Model':<25} | {'Avg Top-1':<12} | {'Avg Top-5':<12} | {'Improvement':<12}")
        print("-" * 70)
        
        base_top1 = None
        for model_name, scores in model_scores.items():
            avg_top1 = np.mean(scores["top1"])
            avg_top5 = np.mean(scores["top5"])
            
            if "base" in model_name.lower() or base_top1 is None:
                base_top1 = avg_top1
                improvement = "-"
            else:
                improvement = f"+{(avg_top1 - base_top1) * 100:.2f}%"
            
            print(f"{model_name:<25} | {avg_top1:<12.4f} | {avg_top5:<12.4f} | {improvement:<12}")
        
        return model_scores
    
    def test_semantic_similarity(self):
        """Test semantic similarity between related queries."""
        print("\n" + "=" * 70)
        print("Semantic Similarity Test (Related Queries)")
        print("=" * 70)
        
        # Pairs of semantically similar queries
        similar_pairs = [
            ("What is the remote work policy?", "Can I work from home?"),
            ("How many vacation days?", "What is my PTO balance?"),
            ("NDA requirements", "Non-disclosure agreement terms"),
            ("Data privacy policy", "How is personal information protected?"),
            ("Password requirements", "What are the security guidelines?"),
        ]
        
        # Pairs of semantically different queries
        different_pairs = [
            ("What is the remote work policy?", "NDA requirements"),
            ("How many vacation days?", "Password requirements"),
            ("Data privacy policy", "Time off request process"),
        ]
        
        for model_name, model in self.models.items():
            print(f"\n{model_name}:")
            
            # Similar pairs
            similar_scores = []
            for q1, q2 in similar_pairs:
                emb1, emb2 = model.encode([q1, q2])
                sim = util.cos_sim(emb1, emb2).item()
                similar_scores.append(sim)
            
            # Different pairs
            different_scores = []
            for q1, q2 in different_pairs:
                emb1, emb2 = model.encode([q1, q2])
                sim = util.cos_sim(emb1, emb2).item()
                different_scores.append(sim)
            
            print(f"  Similar pairs avg:   {np.mean(similar_scores):.4f}")
            print(f"  Different pairs avg: {np.mean(different_scores):.4f}")
            print(f"  Separation:          {np.mean(similar_scores) - np.mean(different_scores):.4f}")


def main():
    """Run comprehensive evaluation."""
    print("=" * 70)
    print("Enhanced Embedding Model Evaluation (v2)")
    print("=" * 70)
    
    script_dir = Path(__file__).parent.absolute()
    backend_dir = script_dir.parent
    
    evaluator = EnhancedEvaluator()
    
    # Load models
    evaluator.load_model("Base (bge-small)", "BAAI/bge-small-en-v1.5")
    
    v1_path = backend_dir / "models" / "policy-embeddings"
    if v1_path.exists():
        evaluator.load_model("Fine-tuned v1", str(v1_path))
    
    v2_path = backend_dir / "models" / "policy-embeddings-v2"
    if v2_path.exists():
        evaluator.load_model("Fine-tuned v2", str(v2_path))
    
    # Load documents
    evaluator.load_documents(str(backend_dir / "sample_docs"))
    
    # Run evaluations
    all_results = evaluator.run_domain_evaluation()
    evaluator.compute_summary(all_results)
    evaluator.test_semantic_similarity()
    
    print("\n" + "=" * 70)
    print("Evaluation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
