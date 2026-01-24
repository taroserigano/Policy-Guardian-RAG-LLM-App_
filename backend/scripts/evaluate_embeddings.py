"""
Evaluate fine-tuned embeddings against base model.
Compares retrieval quality on policy queries.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm


class EmbeddingEvaluator:
    """Compare base vs fine-tuned embeddings."""
    
    def __init__(self, base_model: str, finetuned_model_path: str):
        print(f"📦 Loading models...")
        print(f"   Base: {base_model}")
        print(f"   Fine-tuned: {finetuned_model_path}")
        
        self.base_model = SentenceTransformer(base_model)
        self.finetuned_model = SentenceTransformer(finetuned_model_path)
        
        print(f"✅ Models loaded")
    
    def load_test_data(self, data_path: str, n_samples: int = 100) -> List[Dict]:
        """Load test queries and expected documents."""
        test_data = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= n_samples:
                    break
                test_data.append(json.loads(line))
        
        print(f"📊 Loaded {len(test_data)} test examples")
        return test_data
    
    def compute_similarity(self, model: SentenceTransformer, query: str, document: str) -> float:
        """Compute cosine similarity between query and document."""
        query_emb = model.encode(query, convert_to_tensor=True)
        doc_emb = model.encode(document, convert_to_tensor=True)
        similarity = util.cos_sim(query_emb, doc_emb).item()
        return similarity
    
    def evaluate_retrieval(self, test_data: List[Dict]) -> Dict[str, Dict]:
        """Evaluate retrieval performance."""
        print(f"\n🔍 Evaluating retrieval quality...")
        
        base_scores = []
        finetuned_scores = []
        improvements = []
        
        for example in tqdm(test_data, desc="Computing similarities"):
            query = example['query']
            positive_doc = example['positive']
            
            # Compute similarities
            base_sim = self.compute_similarity(self.base_model, query, positive_doc)
            finetuned_sim = self.compute_similarity(self.finetuned_model, query, positive_doc)
            
            base_scores.append(base_sim)
            finetuned_scores.append(finetuned_sim)
            improvements.append(finetuned_sim - base_sim)
        
        # Compute statistics
        results = {
            "base": {
                "mean": np.mean(base_scores),
                "median": np.median(base_scores),
                "std": np.std(base_scores),
                "min": np.min(base_scores),
                "max": np.max(base_scores)
            },
            "finetuned": {
                "mean": np.mean(finetuned_scores),
                "median": np.median(finetuned_scores),
                "std": np.std(finetuned_scores),
                "min": np.min(finetuned_scores),
                "max": np.max(finetuned_scores)
            },
            "improvement": {
                "mean": np.mean(improvements),
                "median": np.median(improvements),
                "positive_count": sum(1 for x in improvements if x > 0),
                "negative_count": sum(1 for x in improvements if x < 0),
                "percentage_improved": (sum(1 for x in improvements if x > 0) / len(improvements)) * 100
            }
        }
        
        return results
    
    def print_results(self, results: Dict):
        """Print evaluation results."""
        print("\n" + "=" * 70)
        print("📊 Evaluation Results")
        print("=" * 70)
        
        print("\n🔵 Base Model Performance:")
        print(f"   Mean Similarity: {results['base']['mean']:.4f}")
        print(f"   Median: {results['base']['median']:.4f}")
        print(f"   Std Dev: {results['base']['std']:.4f}")
        print(f"   Range: [{results['base']['min']:.4f}, {results['base']['max']:.4f}]")
        
        print("\n🟢 Fine-tuned Model Performance:")
        print(f"   Mean Similarity: {results['finetuned']['mean']:.4f}")
        print(f"   Median: {results['finetuned']['median']:.4f}")
        print(f"   Std Dev: {results['finetuned']['std']:.4f}")
        print(f"   Range: [{results['finetuned']['min']:.4f}, {results['finetuned']['max']:.4f}]")
        
        print("\n📈 Improvement:")
        print(f"   Mean Improvement: {results['improvement']['mean']:+.4f}")
        print(f"   Median Improvement: {results['improvement']['median']:+.4f}")
        print(f"   Improved Queries: {results['improvement']['positive_count']} ({results['improvement']['percentage_improved']:.1f}%)")
        print(f"   Degraded Queries: {results['improvement']['negative_count']}")
        
        # Verdict
        if results['improvement']['mean'] > 0.05:
            print("\n✅ VERDICT: Significant improvement! Fine-tuned model is better.")
        elif results['improvement']['mean'] > 0.02:
            print("\n✅ VERDICT: Moderate improvement. Fine-tuned model is better.")
        elif results['improvement']['mean'] > 0:
            print("\n⚠️  VERDICT: Slight improvement. Consider more training data.")
        else:
            print("\n❌ VERDICT: No improvement. Check training data quality.")
    
    def test_sample_queries(self):
        """Test on sample policy queries."""
        print("\n" + "=" * 70)
        print("🧪 Sample Query Tests")
        print("=" * 70)
        
        test_queries = [
            ("What is the remote work policy?", "remote_work_policy.txt"),
            ("How many vacation days do employees get?", "employee_leave_policy.txt"),
            ("What is required for NDA signing?", "non_disclosure_agreement.txt"),
            ("Can I work from home full-time?", "remote_work_policy.txt"),
            ("What are the data protection requirements?", "data_privacy_policy.txt")
        ]
        
        # Load documents
        docs_dir = Path("../sample_docs")
        documents = {}
        for file_path in docs_dir.glob("*.txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                documents[file_path.name] = f.read()[:1000]  # First 1000 chars
        
        for query, expected_doc in test_queries:
            if expected_doc not in documents:
                continue
            
            doc = documents[expected_doc]
            
            base_sim = self.compute_similarity(self.base_model, query, doc)
            finetuned_sim = self.compute_similarity(self.finetuned_model, query, doc)
            
            print(f"\n📝 Query: {query}")
            print(f"   Expected Doc: {expected_doc}")
            print(f"   Base Similarity: {base_sim:.4f}")
            print(f"   Fine-tuned Similarity: {finetuned_sim:.4f}")
            print(f"   Improvement: {finetuned_sim - base_sim:+.4f}")


def main():
    """Run evaluation."""
    print("=" * 70)
    print("🚀 Policy RAG - Embedding Evaluation")
    print("=" * 70)
    
    # Configuration - use absolute paths
    script_dir = Path(__file__).parent.absolute()
    backend_dir = script_dir.parent
    base_model = "BAAI/bge-small-en-v1.5"
    finetuned_model = str(backend_dir / "models" / "policy-embeddings")
    test_data_path = str(backend_dir / "training_data" / "policy_pairs.jsonl")
    
    # Initialize evaluator
    evaluator = EmbeddingEvaluator(base_model, finetuned_model)
    
    # Load test data
    test_data = evaluator.load_test_data(test_data_path, n_samples=100)
    
    # Evaluate
    results = evaluator.evaluate_retrieval(test_data)
    evaluator.print_results(results)
    
    # Sample queries
    evaluator.test_sample_queries()
    
    print("\n" + "=" * 70)
    print("✨ Evaluation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
