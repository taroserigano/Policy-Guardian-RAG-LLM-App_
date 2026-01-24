"""
Fine-tune sentence-transformers model on policy document data.
Uses contrastive learning with in-batch negatives.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from pathlib import Path
from typing import List, Tuple
import torch
from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
from torch.utils.data import DataLoader
from tqdm import tqdm


class EmbeddingFineTuner:
    """Fine-tune embeddings for policy documents."""
    
    def __init__(self, base_model: str = "BAAI/bge-small-en-v1.5", output_dir: str = "../models/policy-embeddings"):
        """
        Initialize fine-tuner.
        
        Args:
            base_model: Base model to fine-tune (small, fast, good quality)
            output_dir: Where to save fine-tuned model
        """
        self.base_model_name = base_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📦 Loading base model: {base_model}")
        self.model = SentenceTransformer(base_model)
        print(f"✅ Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        
    def load_training_data(self, data_path: str) -> List[InputExample]:
        """Load training pairs from JSONL."""
        print(f"\n📂 Loading training data from: {data_path}")
        examples = []
        
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                # Create positive pair (query -> document)
                example = InputExample(
                    texts=[data['query'], data['positive']],
                    label=1.0  # Positive pair
                )
                examples.append(example)
        
        print(f"✅ Loaded {len(examples)} training examples")
        return examples
    
    def create_evaluation_set(self, examples: List[InputExample], eval_ratio: float = 0.15) -> Tuple[List[InputExample], List[InputExample]]:
        """Split into train and evaluation sets."""
        import random
        random.shuffle(examples)
        
        split_idx = int(len(examples) * (1 - eval_ratio))
        train_examples = examples[:split_idx]
        eval_examples = examples[split_idx:]
        
        print(f"\n📊 Split data:")
        print(f"   Training: {len(train_examples)}")
        print(f"   Evaluation: {len(eval_examples)}")
        
        return train_examples, eval_examples
    
    def create_evaluator(self, eval_examples: List[InputExample]):
        """Create evaluator for tracking progress."""
        queries = [ex.texts[0] for ex in eval_examples]
        documents = [ex.texts[1] for ex in eval_examples]
        scores = [ex.label for ex in eval_examples]
        
        return EmbeddingSimilarityEvaluator(
            queries, documents, scores,
            name="policy-eval",
            show_progress_bar=True
        )
    
    def train(
        self,
        train_examples: List[InputExample],
        evaluator=None,
        epochs: int = 3,
        batch_size: int = 16,
        warmup_steps: int = 100
    ):
        """Fine-tune the model."""
        print(f"\n🔥 Starting training...")
        print(f"   Epochs: {epochs}")
        print(f"   Batch size: {batch_size}")
        print(f"   Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
        
        # Create dataloader
        train_dataloader = DataLoader(
            train_examples,
            shuffle=True,
            batch_size=batch_size
        )
        
        # Use MultipleNegativesRankingLoss for contrastive learning
        # This is very effective for retrieval tasks
        train_loss = losses.MultipleNegativesRankingLoss(self.model)
        
        # Train
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            evaluator=evaluator,
            epochs=epochs,
            warmup_steps=warmup_steps,
            output_path=str(self.output_dir),
            show_progress_bar=True,
            evaluation_steps=500,
            save_best_model=False  # We'll save manually
        )
        
        # Always save the model after training
        print(f"\n💾 Saving model to: {self.output_dir}")
        self.model.save(str(self.output_dir))
        
        print(f"\n✅ Training complete!")
        print(f"   Model saved to: {self.output_dir}")
    
    def test_model(self, test_queries: List[str] = None):
        """Quick test of fine-tuned model."""
        if test_queries is None:
            test_queries = [
                "What is the remote work policy?",
                "How many vacation days do I get?",
                "What documents do I need for NDA?",
                "Can I work from home?",
                "What is the leave policy?"
            ]
        
        print(f"\n🧪 Testing fine-tuned model...")
        embeddings = self.model.encode(test_queries, show_progress_bar=False)
        
        print(f"✅ Generated embeddings for {len(test_queries)} queries")
        print(f"   Embedding shape: {embeddings.shape}")
        print(f"   Sample query: '{test_queries[0]}'")
        print(f"   Embedding preview: [{embeddings[0][:5]}...]")


def main():
    """Main training pipeline."""
    print("=" * 70)
    print("🚀 Policy RAG - Embedding Fine-Tuning")
    print("=" * 70)
    
    # Configuration - use absolute paths
    script_dir = Path(__file__).parent.absolute()
    backend_dir = script_dir.parent
    training_data_path = backend_dir / "training_data" / "policy_pairs.jsonl"
    base_model = "BAAI/bge-small-en-v1.5"  # 33M params, fast, good quality
    output_dir = backend_dir / "models" / "policy-embeddings"
    
    # Training parameters
    epochs = 3
    batch_size = 16
    eval_ratio = 0.15
    
    # Initialize fine-tuner
    fine_tuner = EmbeddingFineTuner(base_model=base_model, output_dir=output_dir)
    
    # Load and split data
    all_examples = fine_tuner.load_training_data(training_data_path)
    train_examples, eval_examples = fine_tuner.create_evaluation_set(all_examples, eval_ratio)
    
    # Create evaluator
    evaluator = fine_tuner.create_evaluator(eval_examples)
    
    # Train
    fine_tuner.train(
        train_examples,
        evaluator=evaluator,
        epochs=epochs,
        batch_size=batch_size
    )
    
    # Test
    fine_tuner.test_model()
    
    print("\n" + "=" * 70)
    print("✨ Fine-tuning complete!")
    print("=" * 70)
    print(f"\n📁 Model saved to: {output_dir}")
    print(f"   Next step: python scripts/convert_to_ollama.py")


if __name__ == "__main__":
    main()
