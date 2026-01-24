"""
Enhanced training data generator for policy/legal/compliance embeddings.
Generates more diverse, domain-specific training pairs with hard negatives.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import random
from pathlib import Path
from typing import List, Dict, Tuple
import requests
from tqdm import tqdm
import re


# Policy/Legal domain-specific terminology for augmentation
POLICY_SYNONYMS = {
    # Employment terms
    "employee": ["staff member", "team member", "worker", "personnel", "associate"],
    "employer": ["company", "organization", "firm", "business"],
    "employment": ["work", "job", "position", "role"],
    
    # Policy terms
    "policy": ["guideline", "procedure", "rule", "regulation", "standard"],
    "comply": ["adhere to", "follow", "abide by", "conform to"],
    "compliance": ["adherence", "conformance", "accordance"],
    "violation": ["breach", "infringement", "non-compliance"],
    
    # Leave/Time off
    "leave": ["time off", "absence", "days off"],
    "vacation": ["annual leave", "holiday", "PTO", "paid time off"],
    "sick leave": ["medical leave", "illness absence", "health leave"],
    
    # Remote work
    "work from home": ["WFH", "remote work", "telecommute", "telework"],
    "remote": ["offsite", "virtual", "distributed"],
    "office": ["workplace", "work site", "premises"],
    
    # Legal terms
    "confidential": ["proprietary", "private", "sensitive", "classified"],
    "disclose": ["reveal", "share", "divulge", "release"],
    "agreement": ["contract", "arrangement", "understanding"],
    "terminate": ["end", "cancel", "discontinue"],
    "obligation": ["duty", "responsibility", "requirement"],
    
    # Data/Security
    "data": ["information", "records", "files"],
    "security": ["protection", "safeguarding", "defense"],
    "breach": ["compromise", "unauthorized access", "leak"],
    "personal information": ["PII", "personal data", "private information"],
    
    # Approval/Process
    "approval": ["authorization", "permission", "consent"],
    "request": ["application", "petition", "submission"],
    "manager": ["supervisor", "lead", "director"],
}

# Domain-specific question templates
POLICY_QUESTION_TEMPLATES = [
    # General policy questions
    "What is the company's policy on {topic}?",
    "What are the requirements for {topic}?",
    "How does the {topic} policy work?",
    "What do I need to know about {topic}?",
    "Can you explain the {topic} guidelines?",
    
    # Eligibility/Requirements
    "Who is eligible for {topic}?",
    "What are the eligibility requirements for {topic}?",
    "What qualifies someone for {topic}?",
    
    # Process/Procedure
    "How do I apply for {topic}?",
    "What is the process for {topic}?",
    "What steps do I need to follow for {topic}?",
    "How do I request {topic}?",
    
    # Restrictions/Limits
    "Are there any restrictions on {topic}?",
    "What are the limitations for {topic}?",
    "What is not allowed regarding {topic}?",
    
    # Compliance
    "What happens if I violate the {topic} policy?",
    "What are the consequences of not following {topic} rules?",
    "How is {topic} compliance enforced?",
    
    # Duration/Timing
    "How long does {topic} last?",
    "What is the duration of {topic}?",
    "When does {topic} apply?",
]


class EnhancedTrainingDataGenerator:
    """Generate high-quality training pairs for policy/legal domain."""
    
    def __init__(self, docs_dir: str, ollama_url: str = "http://localhost:11434"):
        self.docs_dir = Path(docs_dir)
        self.ollama_url = ollama_url
        self.all_chunks = []
        self.chunk_metadata = []
        
    def load_documents(self) -> Dict[str, str]:
        """Load all documents from the directory."""
        documents = {}
        for ext in ["*.txt", "*.md"]:
            for file_path in self.docs_dir.glob(ext):
                with open(file_path, 'r', encoding='utf-8') as f:
                    documents[file_path.name] = f.read()
        print(f"Loaded {len(documents)} documents")
        return documents
    
    def extract_topics(self, text: str) -> List[str]:
        """Extract policy-related topics from text."""
        topics = []
        
        # Common policy topics to look for
        topic_patterns = [
            r"remote work", r"work from home", r"WFH",
            r"vacation|PTO|paid time off|annual leave",
            r"sick leave|medical leave",
            r"confidential|NDA|non-disclosure",
            r"data privacy|data protection|GDPR",
            r"security|information security",
            r"employee conduct|code of conduct",
            r"expense|reimbursement",
            r"travel",
            r"equipment|devices",
            r"termination|resignation",
        ]
        
        for pattern in topic_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Extract the matched topic
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    topics.append(match.group().lower())
        
        return list(set(topics))
    
    def chunk_document(self, text: str, chunk_size: int = 400, overlap: int = 100) -> List[str]:
        """Split document into overlapping chunks."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk.split()) >= 50:  # Minimum chunk size
                chunks.append(chunk)
        
        return chunks
    
    def generate_questions_ollama(self, chunk: str, n_questions: int = 3, model: str = "llama3.1:8b") -> List[str]:
        """Generate multiple diverse questions using Ollama."""
        prompt = f"""You are a helpful assistant generating questions for a corporate policy Q&A system.
Based on this policy document excerpt, generate {n_questions} different natural questions that employees might ask to find this information.

Rules:
- Questions should be diverse (different angles, different phrasings)
- Include both specific and general questions
- Use natural language employees would use
- Focus on policy-related queries (eligibility, process, requirements, restrictions)

Excerpt:
{chunk[:600]}

Generate exactly {n_questions} questions, one per line, numbered 1-{n_questions}:"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.8, "num_predict": 200}
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()["response"]
            
            # Parse numbered questions
            questions = []
            for line in result.split('\n'):
                line = line.strip()
                # Remove numbering
                line = re.sub(r'^[\d]+[\.\)]\s*', '', line)
                if line and len(line.split()) >= 4 and '?' in line:
                    questions.append(line)
            
            return questions[:n_questions]
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []
    
    def generate_synthetic_questions(self, chunk: str) -> List[str]:
        """Generate synthetic questions using templates."""
        topics = self.extract_topics(chunk)
        questions = []
        
        for topic in topics[:3]:  # Limit topics per chunk
            # Select random templates
            templates = random.sample(POLICY_QUESTION_TEMPLATES, min(3, len(POLICY_QUESTION_TEMPLATES)))
            for template in templates:
                question = template.format(topic=topic)
                questions.append(question)
        
        return questions
    
    def augment_text(self, text: str) -> List[str]:
        """Generate augmented versions using domain synonyms."""
        augmented = [text]
        
        for original, synonyms in POLICY_SYNONYMS.items():
            if original.lower() in text.lower():
                # Create variations with synonyms
                for syn in random.sample(synonyms, min(2, len(synonyms))):
                    new_text = re.sub(
                        re.escape(original),
                        syn,
                        text,
                        flags=re.IGNORECASE,
                        count=1
                    )
                    if new_text != text:
                        augmented.append(new_text)
                        if len(augmented) >= 3:
                            return augmented
        
        return augmented
    
    def select_hard_negatives(self, positive_idx: int, doc_name: str, n: int = 3) -> List[Tuple[str, float]]:
        """
        Select hard negatives - chunks that are similar but from different contexts.
        Returns (chunk, hardness_score) tuples.
        """
        hard_negatives = []
        
        for i, (chunk, meta) in enumerate(zip(self.all_chunks, self.chunk_metadata)):
            if i == positive_idx:
                continue
            
            # Hard negative: same document type but different section
            if meta['doc_name'] == doc_name and abs(i - positive_idx) > 2:
                hard_negatives.append((chunk, 0.8))  # Hard
            # Medium negative: different document, similar topic
            elif meta['doc_name'] != doc_name:
                # Check for topic overlap
                positive_topics = set(self.extract_topics(self.all_chunks[positive_idx]))
                negative_topics = set(self.extract_topics(chunk))
                if positive_topics & negative_topics:
                    hard_negatives.append((chunk, 0.6))  # Medium-hard
                else:
                    hard_negatives.append((chunk, 0.3))  # Easy
        
        # Sort by hardness and take top n
        hard_negatives.sort(key=lambda x: x[1], reverse=True)
        return hard_negatives[:n]
    
    def generate_training_data(self, max_pairs: int = 1000) -> List[Dict]:
        """Generate comprehensive training data."""
        documents = self.load_documents()
        
        # Chunk all documents
        print("\nChunking documents...")
        for doc_name, content in documents.items():
            chunks = self.chunk_document(content)
            for i, chunk in enumerate(chunks):
                self.all_chunks.append(chunk)
                self.chunk_metadata.append({
                    'doc_name': doc_name,
                    'chunk_idx': i,
                    'topics': self.extract_topics(chunk)
                })
        
        print(f"Created {len(self.all_chunks)} chunks")
        
        training_data = []
        pairs_per_chunk = max(1, max_pairs // len(self.all_chunks))
        
        print(f"\nGenerating {max_pairs} training pairs...")
        for idx, (chunk, meta) in enumerate(tqdm(zip(self.all_chunks, self.chunk_metadata), 
                                                   total=len(self.all_chunks), desc="Processing chunks")):
            
            # 1. Generate LLM questions (best quality)
            llm_questions = self.generate_questions_ollama(chunk, n_questions=3)
            
            # 2. Generate synthetic questions from templates
            synthetic_questions = self.generate_synthetic_questions(chunk)
            
            # 3. Get hard negatives
            hard_negatives = self.select_hard_negatives(idx, meta['doc_name'])
            
            # Combine questions
            all_questions = llm_questions + synthetic_questions
            
            for question in all_questions[:pairs_per_chunk]:
                if not question or len(question.split()) < 3:
                    continue
                
                # Positive pair
                training_data.append({
                    "query": question,
                    "positive": chunk,
                    "source": meta['doc_name'],
                    "type": "positive",
                    "generation": "llm" if question in llm_questions else "synthetic"
                })
                
                # Augmented positive pairs
                for aug_query in self.augment_text(question)[1:2]:  # 1 augmented version
                    training_data.append({
                        "query": aug_query,
                        "positive": chunk,
                        "source": meta['doc_name'],
                        "type": "augmented"
                    })
                
                # Hard negative pairs (for triplet/contrastive learning)
                for neg_chunk, hardness in hard_negatives[:2]:
                    training_data.append({
                        "query": question,
                        "positive": chunk,
                        "negative": neg_chunk,
                        "source": meta['doc_name'],
                        "type": "triplet",
                        "hardness": hardness
                    })
            
            if len(training_data) >= max_pairs:
                break
        
        print(f"\nGenerated {len(training_data)} training examples")
        return training_data[:max_pairs]
    
    def save_training_data(self, data: List[Dict], output_path: str):
        """Save training data to JSONL format."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in data:
                f.write(json.dumps(example) + '\n')
        
        print(f"\nSaved training data to: {output_path}")
        
        # Statistics
        types = {}
        for ex in data:
            t = ex.get('type', 'unknown')
            types[t] = types.get(t, 0) + 1
        
        print(f"\nData Statistics:")
        for t, count in sorted(types.items()):
            print(f"  {t}: {count}")
        
        # Generation method stats
        gen_types = {}
        for ex in data:
            g = ex.get('generation', 'other')
            gen_types[g] = gen_types.get(g, 0) + 1
        
        print(f"\nGeneration Methods:")
        for g, count in sorted(gen_types.items()):
            print(f"  {g}: {count}")


def main():
    """Generate enhanced training data."""
    script_dir = Path(__file__).parent.absolute()
    backend_dir = script_dir.parent
    docs_dir = backend_dir / "sample_docs"
    output_file = backend_dir / "training_data" / "policy_pairs_v2.jsonl"
    
    print("=" * 70)
    print("Enhanced Policy Embedding Training Data Generator")
    print("=" * 70)
    print("\nFeatures:")
    print("  - Multiple questions per chunk (LLM + synthetic)")
    print("  - Domain-specific augmentation (policy/legal synonyms)")
    print("  - Hard negative mining (similar but wrong chunks)")
    print("  - Triplet pairs for better contrastive learning")
    print("=" * 70)
    
    generator = EnhancedTrainingDataGenerator(docs_dir)
    training_data = generator.generate_training_data(max_pairs=800)
    generator.save_training_data(training_data, output_file)
    
    print("\n" + "=" * 70)
    print("Training data generation complete!")
    print("=" * 70)
    print(f"\nNext step: python scripts/finetune_embeddings_v2.py")


if __name__ == "__main__":
    main()
