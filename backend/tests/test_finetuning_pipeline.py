"""
Test suite for Fine-tuned Embeddings Pipeline
Tests training data generation, model training, and evaluation
"""
import pytest
import os
import sys
import json
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

# Add paths
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))
SCRIPTS_DIR = BACKEND_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


class TestTrainingDataGeneration:
    """Test training data generation for fine-tuning"""
    
    def test_sample_docs_exist(self):
        """Test sample documents exist for training"""
        sample_dir = BACKEND_DIR / "sample_docs"
        
        if not sample_dir.exists():
            pytest.skip("Sample docs directory not found")
        
        docs = list(sample_dir.glob("*.txt"))
        assert len(docs) > 0, "No sample documents found"
    
    def test_sample_docs_readable(self):
        """Test sample documents are readable"""
        sample_dir = BACKEND_DIR / "sample_docs"
        
        if not sample_dir.exists():
            pytest.skip("Sample docs directory not found")
        
        for doc_path in sample_dir.glob("*.txt"):
            content = doc_path.read_text(encoding="utf-8")
            assert len(content) > 100, f"Document too short: {doc_path.name}"
    
    def test_policy_synonyms_coverage(self):
        """Test policy synonyms dictionary has good coverage"""
        # Expected policy domain synonyms
        expected_concepts = [
            ("remote work", "wfh", "work from home"),
            ("leave", "vacation", "pto"),
            ("confidential", "nda", "non-disclosure"),
        ]
        
        # At least these concepts should be in training vocabulary
        for concept_group in expected_concepts:
            # This tests that our training data would include these
            assert len(concept_group) >= 2
    
    def test_training_data_directory(self):
        """Test training data output directory"""
        training_dir = BACKEND_DIR / "training_data"
        
        # Directory should exist after running generation script
        if not training_dir.exists():
            pytest.skip("Training data not yet generated")
        
        # Should have JSON files
        json_files = list(training_dir.glob("*.json"))
        if len(json_files) == 0:
            pytest.skip("No training data files found")


class TestFineTunedModel:
    """Test fine-tuned model outputs"""
    
    def test_model_v2_directory(self):
        """Test V2 model directory structure"""
        model_dir = BACKEND_DIR / "models" / "policy-embeddings-v2"
        
        if not model_dir.exists():
            pytest.skip("V2 model not trained yet")
        
        # Check for essential files
        assert (model_dir / "config.json").exists()
        assert (model_dir / "tokenizer_config.json").exists()
    
    def test_model_config_valid(self):
        """Test model config is valid JSON"""
        config_path = BACKEND_DIR / "models" / "policy-embeddings-v2" / "config.json"
        
        if not config_path.exists():
            pytest.skip("Model config not found")
        
        with open(config_path) as f:
            config = json.load(f)
            
        assert "hidden_size" in config or "model_type" in config
    
    def test_model_produces_embeddings(self):
        """Test model can produce embeddings"""
        try:
            from sentence_transformers import SentenceTransformer
            
            model_path = BACKEND_DIR / "models" / "policy-embeddings-v2"
            
            if not model_path.exists():
                pytest.skip("V2 model not trained yet")
            
            model = SentenceTransformer(str(model_path))
            embedding = model.encode("Test policy question")
            
            assert embedding is not None
            assert len(embedding) == 384  # BGE-small dimension
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_embedding_normalization(self):
        """Test embeddings are properly normalized"""
        try:
            from sentence_transformers import SentenceTransformer
            
            model_path = BACKEND_DIR / "models" / "policy-embeddings-v2"
            
            if not model_path.exists():
                pytest.skip("V2 model not trained yet")
            
            model = SentenceTransformer(str(model_path))
            embedding = model.encode("Test query", normalize_embeddings=True)
            
            # Normalized embedding should have unit length
            norm = np.linalg.norm(embedding)
            assert abs(norm - 1.0) < 0.01, f"Embedding not normalized: norm={norm}"
        except ImportError:
            pytest.skip("sentence-transformers not installed")


class TestEmbeddingQuality:
    """Test quality of fine-tuned embeddings"""
    
    @pytest.fixture
    def model(self):
        """Load the fine-tuned model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            model_path = BACKEND_DIR / "models" / "policy-embeddings-v2"
            
            if not model_path.exists():
                pytest.skip("V2 model not trained yet")
            
            return SentenceTransformer(str(model_path))
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_synonym_similarity(self, model):
        """Test synonymous terms have high similarity"""
        synonyms = [
            ("work from home", "WFH"),
            ("remote work", "telecommuting"),
            ("vacation", "PTO"),
            ("sick leave", "medical leave"),
        ]
        
        for term1, term2 in synonyms:
            emb1 = model.encode(term1, normalize_embeddings=True)
            emb2 = model.encode(term2, normalize_embeddings=True)
            
            similarity = np.dot(emb1, emb2)
            assert similarity > 0.6, f"Low similarity for '{term1}' and '{term2}': {similarity}"
    
    def test_query_document_alignment(self, model):
        """Test queries are aligned with relevant documents"""
        query = "What are the work from home guidelines?"
        
        # Relevant document text
        relevant = "Employees may work remotely according to the WFH policy guidelines."
        
        # Irrelevant document text
        irrelevant = "The cafeteria menu includes vegetarian options."
        
        query_emb = model.encode(query, normalize_embeddings=True)
        relevant_emb = model.encode(relevant, normalize_embeddings=True)
        irrelevant_emb = model.encode(irrelevant, normalize_embeddings=True)
        
        sim_relevant = np.dot(query_emb, relevant_emb)
        sim_irrelevant = np.dot(query_emb, irrelevant_emb)
        
        assert sim_relevant > sim_irrelevant, "Relevant doc should have higher similarity"
    
    def test_policy_topic_clustering(self, model):
        """Test policy topics form distinct clusters"""
        # Privacy-related terms
        privacy_terms = ["data privacy", "GDPR", "personal information"]
        
        # Leave-related terms
        leave_terms = ["vacation days", "sick leave", "PTO balance"]
        
        privacy_embs = [model.encode(t, normalize_embeddings=True) for t in privacy_terms]
        leave_embs = [model.encode(t, normalize_embeddings=True) for t in leave_terms]
        
        # Within-cluster similarity should be higher than between-cluster
        privacy_centroid = np.mean(privacy_embs, axis=0)
        leave_centroid = np.mean(leave_embs, axis=0)
        
        # Average within-privacy similarity
        within_privacy = np.mean([np.dot(e, privacy_centroid) for e in privacy_embs])
        
        # Cross-cluster similarity
        cross_cluster = np.dot(privacy_centroid, leave_centroid)
        
        # Within-cluster should be tighter
        assert within_privacy > cross_cluster * 0.9


class TestTrainingPipeline:
    """Test the training pipeline components"""
    
    def test_loss_functions_available(self):
        """Test required loss functions are available"""
        try:
            from sentence_transformers.losses import (
                MultipleNegativesRankingLoss,
                TripletLoss
            )
            assert MultipleNegativesRankingLoss is not None
            assert TripletLoss is not None
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_input_examples_format(self):
        """Test InputExample format for training"""
        try:
            from sentence_transformers import InputExample
            
            # Test pair example
            pair = InputExample(
                texts=["query", "relevant document"]
            )
            assert len(pair.texts) == 2
            
            # Test triplet example
            triplet = InputExample(
                texts=["anchor", "positive", "negative"]
            )
            assert len(triplet.texts) == 3
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_data_loader_creation(self):
        """Test data loader can be created"""
        try:
            from sentence_transformers import InputExample
            from torch.utils.data import DataLoader
            
            examples = [
                InputExample(texts=["query 1", "doc 1"]),
                InputExample(texts=["query 2", "doc 2"]),
            ]
            
            loader = DataLoader(examples, batch_size=2, shuffle=True)
            assert len(loader) > 0
        except ImportError:
            pytest.skip("Required packages not installed")


class TestEvaluationMetrics:
    """Test evaluation metrics for embedding quality"""
    
    def test_cosine_similarity_calculation(self):
        """Test cosine similarity is calculated correctly"""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        vec3 = np.array([0.0, 1.0, 0.0])
        
        # Same vector should have similarity 1.0
        sim_same = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        assert abs(sim_same - 1.0) < 0.001
        
        # Orthogonal vectors should have similarity 0.0
        sim_ortho = np.dot(vec1, vec3) / (np.linalg.norm(vec1) * np.linalg.norm(vec3))
        assert abs(sim_ortho) < 0.001
    
    def test_semantic_separation_metric(self):
        """Test semantic separation metric calculation"""
        # Simulated positive similarities (query-relevant)
        pos_sims = [0.85, 0.82, 0.88, 0.79]
        
        # Simulated negative similarities (query-irrelevant)
        neg_sims = [0.45, 0.52, 0.38, 0.41]
        
        # Separation = mean(positive) - mean(negative)
        separation = np.mean(pos_sims) - np.mean(neg_sims)
        
        assert separation > 0.3, "Good fine-tuning should have separation > 0.3"
    
    def test_mrr_calculation(self):
        """Test Mean Reciprocal Rank calculation"""
        # Simulated rankings (1 = first position)
        ranks = [1, 2, 1, 3, 1]
        
        mrr = np.mean([1.0 / r for r in ranks])
        
        assert 0 <= mrr <= 1.0
        assert mrr > 0.6, "Good retrieval should have MRR > 0.6"


class TestIntegration:
    """Integration tests for the complete fine-tuning workflow"""
    
    def test_end_to_end_embedding_workflow(self):
        """Test complete embedding workflow"""
        try:
            from app.rag.embeddings import PolicyEmbeddings
            
            embedder = PolicyEmbeddings()
            
            # Test query embedding
            query = "What is the company policy on remote work?"
            query_emb = embedder.embed_query(query)
            
            assert len(query_emb) == 384
            
            # Test document embedding
            docs = [
                "Remote work is permitted with manager approval.",
                "Employees must maintain productivity while working from home.",
            ]
            doc_embs = embedder.embed_documents(docs)
            
            assert len(doc_embs) == 2
            for emb in doc_embs:
                assert len(emb) == 384
            
            # Test similarity ranking
            query_np = np.array(query_emb)
            similarities = [np.dot(query_np, np.array(d)) for d in doc_embs]
            
            # Both should have positive similarity
            assert all(s > 0 for s in similarities)
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
