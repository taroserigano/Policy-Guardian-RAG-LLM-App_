"""
Generate training data for embedding fine-tuning from policy documents.
Creates query-document pairs automatically using LLM-based augmentation.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import random
from pathlib import Path
from typing import List, Tuple, Dict
import requests
from tqdm import tqdm


class TrainingDataGenerator:
    """Generate training pairs from policy documents."""
    
    def __init__(self, docs_dir: str, ollama_url: str = "http://localhost:11434"):
        self.docs_dir = Path(docs_dir)
        self.ollama_url = ollama_url
        self.training_pairs = []
        
    def load_documents(self) -> Dict[str, str]:
        """Load all documents from the directory."""
        documents = {}
        for file_path in self.docs_dir.glob("*.txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                documents[file_path.name] = f.read()
        print(f"✅ Loaded {len(documents)} documents")
        return documents
    
    def chunk_document(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split document into chunks for training."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size // 2):  # Overlap
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk.split()) > 50:  # Min chunk size
                chunks.append(chunk)
        return chunks
    
    def generate_query_ollama(self, chunk: str, model: str = "llama3.1:8b") -> str:
        """Generate a question from a chunk using Ollama."""
        prompt = f"""Based on this policy document excerpt, generate a natural question that someone would ask to find this information. Only return the question, nothing else.

Excerpt: {chunk[:300]}...

Question:"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 50}
                },
                timeout=30
            )
            response.raise_for_status()
            question = response.json()["response"].strip()
            # Clean up common prefixes
            question = question.replace("Question:", "").strip()
            question = question.strip('"\'')
            return question
        except Exception as e:
            print(f"⚠️  Error generating question: {e}")
            return None
    
    def generate_paraphrases(self, text: str, n: int = 3) -> List[str]:
        """Generate paraphrased versions of text."""
        # Simple rule-based paraphrasing for speed
        paraphrases = [text]
        
        # Synonym replacements for policy terms
        synonyms = {
            "employee": ["team member", "staff", "personnel"],
            "policy": ["guideline", "rule", "procedure"],
            "work from home": ["remote work", "telecommute", "WFH"],
            "leave": ["time off", "absence", "PTO"],
            "vacation": ["annual leave", "holiday", "time off"],
        }
        
        for original, replacements in synonyms.items():
            if original.lower() in text.lower():
                for replacement in replacements[:n-1]:
                    new_text = text.replace(original, replacement)
                    if new_text != text:
                        paraphrases.append(new_text)
        
        return paraphrases[:n]
    
    def create_hard_negatives(self, chunks: List[str], positive_idx: int, n: int = 2) -> List[str]:
        """Select hard negative examples (similar but different chunks)."""
        negatives = []
        available = [i for i in range(len(chunks)) if i != positive_idx]
        for idx in random.sample(available, min(n, len(available))):
            negatives.append(chunks[idx])
        return negatives
    
    def generate_training_data(self, max_pairs: int = 500) -> List[Dict]:
        """Generate training data with queries and documents."""
        documents = self.load_documents()
        all_chunks = []
        chunk_sources = []
        
        # Chunk all documents
        print("\n📄 Chunking documents...")
        for doc_name, content in documents.items():
            chunks = self.chunk_document(content)
            all_chunks.extend(chunks)
            chunk_sources.extend([doc_name] * len(chunks))
        
        print(f"✅ Created {len(all_chunks)} chunks")
        
        # Generate queries for chunks
        print(f"\n🤖 Generating {max_pairs} training pairs using Ollama...")
        training_data = []
        
        # Sample chunks to get desired number of pairs
        sampled_indices = random.sample(range(len(all_chunks)), min(max_pairs, len(all_chunks)))
        
        for idx in tqdm(sampled_indices, desc="Generating queries"):
            chunk = all_chunks[idx]
            
            # Generate query
            query = self.generate_query_ollama(chunk)
            if not query or len(query.split()) < 3:
                continue
            
            # Create training example
            example = {
                "query": query,
                "positive": chunk,
                "source": chunk_sources[idx],
                "type": "generated"
            }
            training_data.append(example)
            
            # Add paraphrased versions
            paraphrases = self.generate_paraphrases(query)
            for para in paraphrases[1:]:  # Skip original
                training_data.append({
                    "query": para,
                    "positive": chunk,
                    "source": chunk_sources[idx],
                    "type": "paraphrase"
                })
        
        print(f"\n✅ Generated {len(training_data)} training examples")
        return training_data
    
    def save_training_data(self, data: List[Dict], output_path: str):
        """Save training data to JSONL format."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in data:
                f.write(json.dumps(example) + '\n')
        
        print(f"\n💾 Saved training data to: {output_path}")
        print(f"   Total examples: {len(data)}")
        
        # Print statistics
        types = {}
        for ex in data:
            types[ex['type']] = types.get(ex['type'], 0) + 1
        
        print(f"\n📊 Data Statistics:")
        for t, count in types.items():
            print(f"   {t}: {count}")


def main():
    """Generate training data from sample documents."""
    # Configuration - use absolute paths
    script_dir = Path(__file__).parent.absolute()
    backend_dir = script_dir.parent
    docs_dir = backend_dir / "sample_docs"
    output_file = backend_dir / "training_data" / "policy_pairs.jsonl"
    max_pairs = 300  # Adjust based on compute resources
    
    print("=" * 60)
    print("🚀 Policy RAG - Embedding Training Data Generator")
    print("=" * 60)
    
    # Generate data
    generator = TrainingDataGenerator(docs_dir)
    training_data = generator.generate_training_data(max_pairs=max_pairs)
    
    # Save
    generator.save_training_data(training_data, output_file)
    
    print("\n" + "=" * 60)
    print("✨ Training data generation complete!")
    print("=" * 60)
    print(f"\n📁 Output: {output_file}")
    print(f"   Next step: python scripts/finetune_embeddings.py")


if __name__ == "__main__":
    main()
