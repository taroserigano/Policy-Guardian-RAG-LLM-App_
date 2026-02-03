# 🚀 Embedding Fine-Tuning Guide

## Overview

Fine-tune embeddings to understand policy document terminology better than generic models.

## Pipeline Steps

### 1️⃣ Generate Training Data

Automatically creates query-document pairs from your policy documents.

```bash
cd backend
python scripts/generate_training_data.py
```

**What it does:**

- Loads documents from `sample_docs/`
- Chunks documents into 500-word segments
- Uses Ollama LLM to generate questions for each chunk
- Creates paraphrased versions for data augmentation
- Saves to `training_data/policy_pairs.jsonl`

**Output:** ~300-500 training pairs

---

### 2️⃣ Fine-Tune Model

Trains sentence-transformers model on your policy data.

```bash
python scripts/finetune_embeddings.py
```

**What it does:**

- Loads base model: `BAAI/bge-small-en-v1.5` (33M params)
- Splits data: 85% training, 15% evaluation
- Uses contrastive learning (MultipleNegativesRankingLoss)
- Trains for 3 epochs with evaluation checkpoints
- Saves best model to `models/policy-embeddings/`

**Requirements:**

- ~2GB RAM for CPU training
- ~1-2 hours on CPU, ~10-15 min on GPU
- PyTorch + sentence-transformers

---

### 3️⃣ Evaluate Model

Compares fine-tuned vs base model on retrieval quality.

```bash
python scripts/evaluate_embeddings.py
```

**What it measures:**

- Mean cosine similarity for query-document pairs
- Improvement percentage
- Sample query tests on actual policy questions

**Expected results:**

- Mean similarity improvement: +0.05 to +0.15
- 70-90% of queries show improvement

---

### 4️⃣ Deploy Model

Creates FastAPI wrapper for serving embeddings.

```bash
python scripts/convert_to_ollama.py
```

**What it creates:**

- `models/embedding_server.py` - FastAPI wrapper
- OpenAI-compatible `/v1/embeddings` endpoint
- Health check endpoint

**Start the server:**

```bash
cd backend/models
python embedding_server.py
# Server runs on http://localhost:8001
```

---

### 5️⃣ Integrate with RAG

**Update `app/rag/embeddings.py`:**

```python
class PolicyEmbeddings:
    """Fine-tuned embeddings for policy documents."""

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('../models/policy-embeddings')

    def embed_text(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()

# Add to get_embeddings() function
def get_embeddings(provider: str = "openai"):
    if provider == "policy":
        return PolicyEmbeddings()
    # ... rest of code
```

**Update `frontend/src/components/ModelPicker.jsx`:**

Add to embedding dropdown:

```jsx
<option value="policy">Policy (Fine-tuned)</option>
```

---

## Quick Start (All Steps)

```bash
# Install dependencies
pip install -r requirements-finetuning.txt

# Run full pipeline
cd backend

# 1. Generate data
python scripts/generate_training_data.py

# 2. Train model
python scripts/finetune_embeddings.py

# 3. Evaluate
python scripts/evaluate_embeddings.py

# 4. Deploy
python scripts/convert_to_ollama.py

# 5. Start embedding server
cd models
python embedding_server.py
```

---

## Configuration

**Training Data (`generate_training_data.py`):**

- `max_pairs`: 300 (default) - increase for more data
- `chunk_size`: 500 words
- `ollama_model`: "llama3.1:8b" - for question generation

**Fine-Tuning (`finetune_embeddings.py`):**

- `base_model`: "BAAI/bge-small-en-v1.5" (384 dims)
- `epochs`: 3
- `batch_size`: 16 (reduce to 8 if OOM)
- `eval_ratio`: 0.15

**Alternative Base Models:**

- `sentence-transformers/all-MiniLM-L6-v2` (384 dims, faster)
- `BAAI/bge-base-en-v1.5` (768 dims, higher quality)
- `thenlper/gte-small` (384 dims, good balance)

---

## Performance Expectations

| Metric          | Base Model | Fine-Tuned      | Improvement |
| --------------- | ---------- | --------------- | ----------- |
| Avg Similarity  | 0.55       | 0.65            | +18%        |
| Top-3 Accuracy  | 72%        | 88%             | +16%        |
| Training Time   | -          | 1-2 hours (CPU) | -           |
| Inference Speed | Same       | Same            | No change   |

---

## Troubleshooting

**OOM Error during training:**

```python
# Reduce batch size in finetune_embeddings.py
batch_size = 8  # or 4
```

**Ollama not generating questions:**

- Ensure Ollama is running: `ollama serve`
- Check model is available: `ollama list`
- Pull model if needed: `ollama pull llama3.1:8b`

**No improvement after training:**

- Generate more training data (increase `max_pairs`)
- Use more epochs (5-10)
- Try different base model
- Check data quality in `policy_pairs.jsonl`

---

## Next Steps

After embedding fine-tuning:

1. **Hybrid Search** - Combine embeddings with BM25 keyword search
2. **Reranking** - Add cross-encoder reranker for top results
3. **LLM Fine-Tuning** - Fine-tune answer generation (separate from retrieval)
4. **Active Learning** - Collect user feedback to improve embeddings

---

## Files Created

```
backend/
├── scripts/
│   ├── generate_training_data.py   # Data generation
│   ├── finetune_embeddings.py      # Training script
│   ├── evaluate_embeddings.py      # Evaluation
│   └── convert_to_ollama.py        # Deployment
├── training_data/
│   └── policy_pairs.jsonl          # Training data
├── models/
│   ├── policy-embeddings/          # Fine-tuned model
│   └── embedding_server.py         # FastAPI wrapper
└── requirements-finetuning.txt     # Dependencies
```

---

## Benefits

✅ **Better Retrieval** - Understands policy-specific terms (PTO, WFH, NDA)  
✅ **Domain-Specific** - Trained on your actual documents  
✅ **Fast Inference** - Same speed as base model  
✅ **Drop-in Replacement** - Works with existing RAG pipeline  
✅ **Cost-Effective** - Train once, use forever (no API costs)  
✅ **Privacy** - Runs locally, no data leaves your system
