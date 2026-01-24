"""
Enhanced fine-tuning script for policy/legal/compliance embeddings.
Uses triplet loss with hard negatives and longer training.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from pathlib import Path
from typing import List, Tuple
import torch
from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator, TripletEvaluator
from torch.utils.data import DataLoader
from tqdm import tqdm
import random


class EnhancedEmbeddingFineTuner:
    """Fine-tune embeddings with advanced techniques for policy domain."""
    
    def __init__(self, base_model: str = "BAAI/bge-small-en-v1.5", output_dir: str = "../models/policy-embeddings-v2"):
        """
        Initialize fine-tuner.
        
        Args:
            base_model: Base model to fine-tune
            output_dir: Where to save fine-tuned model
        """
        self.base_model_name = base_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Loading base model: {base_model}")
        self.model = SentenceTransformer(base_model)
        print(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        
    def load_training_data(self, data_path: str) -> Tuple[List[InputExample], List[InputExample]]:
        """Load and separate positive pairs from triplets."""
        print(f"\nLoading training data from: {data_path}")
        
        positive_examples = []
        triplet_examples = []
        
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                
                if data.get('type') == 'triplet' and 'negative' in data:
                    # Triplet: (anchor, positive, negative)
                    example = InputExample(
                        texts=[data['query'], data['positive'], data['negative']]
                    )
                    triplet_examples.append(example)
                else:
                    # Positive pair
                    example = InputExample(
                        texts=[data['query'], data['positive']],
                        label=1.0
                    )
                    positive_examples.append(example)
        
        print(f"Loaded {len(positive_examples)} positive pairs")
        print(f"Loaded {len(triplet_examples)} triplet examples")
        return positive_examples, triplet_examples
    
    def create_evaluation_set(self, examples: List[InputExample], eval_ratio: float = 0.1) -> Tuple[List[InputExample], List[InputExample]]:
        """Split into train and evaluation sets."""
        random.shuffle(examples)
        split_idx = int(len(examples) * (1 - eval_ratio))
        return examples[:split_idx], examples[split_idx:]
    
    def train_two_phase(
        self,
        positive_examples: List[InputExample],
        triplet_examples: List[InputExample],
        epochs_phase1: int = 3,
        epochs_phase2: int = 3,
        batch_size: int = 16
    ):
        """
        Two-phase training:
        Phase 1: MultipleNegativesRankingLoss on positive pairs (learn what's similar)
        Phase 2: TripletLoss on triplets with hard negatives (learn what's different)
        """
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"\nTraining device: {device}")
        
        # ===== PHASE 1: Contrastive learning with in-batch negatives =====
        print("\n" + "=" * 60)
        print("PHASE 1: Contrastive Learning (in-batch negatives)")
        print("=" * 60)
        
        train_pos, eval_pos = self.create_evaluation_set(positive_examples, 0.1)
        print(f"Phase 1 Training: {len(train_pos)} examples")
        
        train_dataloader = DataLoader(train_pos, shuffle=True, batch_size=batch_size)
        train_loss = losses.MultipleNegativesRankingLoss(self.model)
        
        # Evaluator for phase 1
        eval_queries = [ex.texts[0] for ex in eval_pos]
        eval_docs = [ex.texts[1] for ex in eval_pos]
        eval_scores = [1.0] * len(eval_pos)
        evaluator = EmbeddingSimilarityEvaluator(eval_queries, eval_docs, eval_scores, name="phase1-eval")
        
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            evaluator=evaluator,
            epochs=epochs_phase1,
            warmup_steps=int(len(train_dataloader) * 0.1),
            output_path=str(self.output_dir / "phase1"),
            show_progress_bar=True,
            evaluation_steps=200,
            save_best_model=False
        )
        
        print("\nPhase 1 complete!")
        
        # ===== PHASE 2: Triplet learning with hard negatives =====
        if triplet_examples:
            print("\n" + "=" * 60)
            print("PHASE 2: Triplet Learning (hard negatives)")
            print("=" * 60)
            
            train_trip, eval_trip = self.create_evaluation_set(triplet_examples, 0.1)
            print(f"Phase 2 Training: {len(train_trip)} triplets")
            
            triplet_dataloader = DataLoader(train_trip, shuffle=True, batch_size=batch_size)
            
            # TripletLoss with margin
            triplet_loss = losses.TripletLoss(
                model=self.model,
                distance_metric=losses.TripletDistanceMetric.COSINE,
                triplet_margin=0.3  # Margin between positive and negative
            )
            
            # Triplet evaluator
            if eval_trip:
                anchors = [ex.texts[0] for ex in eval_trip]
                positives = [ex.texts[1] for ex in eval_trip]
                negatives = [ex.texts[2] for ex in eval_trip]
                trip_evaluator = TripletEvaluator(anchors, positives, negatives, name="phase2-eval")
            else:
                trip_evaluator = None
            
            self.model.fit(
                train_objectives=[(triplet_dataloader, triplet_loss)],
                evaluator=trip_evaluator,
                epochs=epochs_phase2,
                warmup_steps=int(len(triplet_dataloader) * 0.1),
                output_path=str(self.output_dir / "phase2"),
                show_progress_bar=True,
                evaluation_steps=200,
                save_best_model=False
            )
            
            print("\nPhase 2 complete!")
        
        # Save final model
        print(f"\nSaving final model to: {self.output_dir}")
        self.model.save(str(self.output_dir))
        
        print("\nTraining complete!")
    
    def test_model(self):
        """Test the fine-tuned model on policy-specific queries."""
        print("\n" + "=" * 60)
        print("Testing Fine-Tuned Model")
        print("=" * 60)
        
        # Policy-specific test queries
        test_queries = [
            # Remote work
            "What is the WFH policy?",
            "Can I work from home full time?",
            "Remote work guidelines",
            
            # Leave
            "How many vacation days do I get?",
            "PTO policy",
            "Sick leave requirements",
            
            # Confidentiality
            "NDA requirements",
            "What is considered confidential information?",
            "Non-disclosure agreement terms",
            
            # Data privacy
            "Data protection policy",
            "How is personal information handled?",
            "GDPR compliance requirements",
            
            # General
            "Employee code of conduct",
            "What happens if I violate company policy?",
        ]
        
        print("\nGenerating embeddings for test queries...")
        embeddings = self.model.encode(test_queries, show_progress_bar=False)
        
        print(f"Generated {len(embeddings)} embeddings")
        print(f"Embedding dimension: {embeddings.shape[1]}")
        
        # Show sample embeddings
        print("\nSample queries and embedding norms:")
        for i, (query, emb) in enumerate(zip(test_queries[:5], embeddings[:5])):
            norm = (emb ** 2).sum() ** 0.5
            print(f"  '{query[:40]}...' -> norm: {norm:.4f}")


def main():
    """Main training pipeline."""
    print("=" * 70)
    print("Enhanced Policy Embedding Fine-Tuning (v2)")
    print("=" * 70)
    print("\nImprovements over v1:")
    print("  - Two-phase training (contrastive + triplet)")
    print("  - Hard negative mining")
    print("  - More training data")
    print("  - Longer training")
    print("=" * 70)
    
    # Configuration
    script_dir = Path(__file__).parent.absolute()
    backend_dir = script_dir.parent
    training_data_path = backend_dir / "training_data" / "policy_pairs_v2.jsonl"
    output_dir = backend_dir / "models" / "policy-embeddings-v2"
    
    # Use a good base model for document retrieval
    base_model = "BAAI/bge-small-en-v1.5"  # 33M params, great for retrieval
    
    # Training parameters
    epochs_phase1 = 4  # More epochs for phase 1
    epochs_phase2 = 3  # Triplet learning
    batch_size = 16
    
    # Initialize
    fine_tuner = EnhancedEmbeddingFineTuner(base_model=base_model, output_dir=str(output_dir))
    
    # Load data
    positive_examples, triplet_examples = fine_tuner.load_training_data(str(training_data_path))
    
    # Train
    fine_tuner.train_two_phase(
        positive_examples,
        triplet_examples,
        epochs_phase1=epochs_phase1,
        epochs_phase2=epochs_phase2,
        batch_size=batch_size
    )
    
    # Test
    fine_tuner.test_model()
    
    print("\n" + "=" * 70)
    print("Fine-tuning complete!")
    print("=" * 70)
    print(f"\nModel saved to: {output_dir}")
    print(f"\nNext step: python scripts/evaluate_embeddings_v2.py")


if __name__ == "__main__":
    main()
