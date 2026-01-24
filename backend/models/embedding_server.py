"""
FastAPI wrapper for fine-tuned embeddings.
Makes the model compatible with OpenAI-style API.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from typing import List
import uvicorn

app = FastAPI(title="Policy Embeddings API")

# Load model
MODEL_PATH = "../models/policy-embeddings"
model = SentenceTransformer(MODEL_PATH)

class EmbeddingRequest(BaseModel):
    input: str | List[str]
    model: str = "policy-embeddings"

class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[dict]
    model: str
    usage: dict

@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """Generate embeddings (OpenAI-compatible endpoint)."""
    try:
        # Handle single string or list
        texts = [request.input] if isinstance(request.input, str) else request.input
        
        # Generate embeddings
        embeddings = model.encode(texts, show_progress_bar=False)
        
        # Format response
        data = [
            {
                "object": "embedding",
                "embedding": emb.tolist(),
                "index": i
            }
            for i, emb in enumerate(embeddings)
        ]
        
        return EmbeddingResponse(
            data=data,
            model=request.model,
            usage={
                "prompt_tokens": sum(len(t.split()) for t in texts),
                "total_tokens": sum(len(t.split()) for t in texts)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "model": "policy-embeddings"}

if __name__ == "__main__":
    print("🚀 Starting Policy Embeddings API on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
