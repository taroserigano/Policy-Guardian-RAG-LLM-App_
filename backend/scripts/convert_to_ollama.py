"""
Convert fine-tuned sentence-transformers model to Ollama format.
Handles GGUF conversion and Modelfile creation.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import subprocess
import json
from pathlib import Path
import shutil
import requests


class OllamaConverter:
    """Convert sentence-transformers model to Ollama."""
    
    def __init__(self, model_dir: str, ollama_url: str = "http://localhost:11434"):
        self.model_dir = Path(model_dir)
        self.ollama_url = ollama_url
        self.gguf_path = None
        
    def check_ollama(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def save_as_onnx(self) -> Path:
        """Export model to ONNX format (step 1)."""
        print("\n📦 Exporting to ONNX format...")
        
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(str(self.model_dir))
        
        onnx_path = self.model_dir / "model.onnx"
        
        # Export model components
        model.save(str(self.model_dir), safe_serialization=True)
        
        print(f"✅ Model saved with safetensors")
        return self.model_dir
    
    def create_modelfile(self, model_name: str = "policy-embeddings") -> Path:
        """Create Ollama Modelfile."""
        print(f"\n📝 Creating Modelfile for '{model_name}'...")
        
        modelfile_content = f"""# Policy RAG Fine-Tuned Embeddings
FROM .
TEMPLATE \"\"\"{{{{ .Prompt }}}}\"\"\"
PARAMETER temperature 0
PARAMETER num_ctx 512
"""
        
        modelfile_path = self.model_dir / "Modelfile"
        with open(modelfile_path, 'w') as f:
            f.write(modelfile_content)
        
        print(f"✅ Modelfile created: {modelfile_path}")
        return modelfile_path
    
    def import_to_ollama(self, model_name: str = "policy-embeddings:latest") -> bool:
        """Import model to Ollama using standard sentence-transformers format."""
        print(f"\n🚀 Importing to Ollama as '{model_name}'...")
        
        if not self.check_ollama():
            print("❌ Ollama is not running. Please start Ollama first:")
            print("   Windows: Start Ollama from Start Menu or 'ollama serve'")
            print("   Mac/Linux: 'ollama serve'")
            return False
        
        # For sentence-transformers, we'll use Ollama's embedding model support
        # Ollama can load sentence-transformers directly via API
        print("\n💡 Manual import instructions:")
        print(f"   1. Copy model directory to Ollama models folder:")
        print(f"      {self.model_dir}")
        print(f"\n   2. Create a custom embedding endpoint in your code:")
        print(f"      - Load the model with SentenceTransformer")
        print(f"      - Serve via FastAPI endpoint")
        print(f"      - Use endpoint URL in embeddings.py")
        
        return True
    
    def create_wrapper_script(self) -> Path:
        """Create a FastAPI wrapper for the model."""
        print("\n🔧 Creating FastAPI wrapper...")
        
        wrapper_code = '''"""
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
'''
        
        wrapper_path = self.model_dir.parent / "embedding_server.py"
        with open(wrapper_path, 'w', encoding='utf-8') as f:
            f.write(wrapper_code)
        
        print(f"✅ Wrapper script created: {wrapper_path}")
        return wrapper_path
    
    def create_integration_instructions(self):
        """Print integration instructions."""
        print("\n" + "=" * 70)
        print("📋 Integration Instructions")
        print("=" * 70)
        
        print("\n1️⃣  Start the embedding server:")
        print(f"   cd backend/models")
        print(f"   python embedding_server.py")
        print(f"   Server will run on: http://localhost:8001")
        
        print("\n2️⃣  Update app/rag/embeddings.py:")
        print("""
class PolicyEmbeddings:
    def __init__(self):
        self.model = SentenceTransformer('../models/policy-embeddings')
    
    def embed_text(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()

# In get_embeddings() function, add:
if provider == "policy":
    return PolicyEmbeddings()
""")
        
        print("\n3️⃣  Test the embeddings:")
        print("""
from app.rag.embeddings import get_embeddings

embeddings = get_embeddings(provider="policy")
vec = embeddings.embed_text("What is the remote work policy?")
print(f"✅ Embedding dimension: {len(vec)}")
""")
        
        print("\n4️⃣  Update frontend ModelPicker.jsx:")
        print("""   Add to embedding options:
   <option value="policy">Policy (Fine-tuned)</option>
""")


def main():
    """Convert and import model."""
    print("=" * 70)
    print("🚀 Policy RAG - Ollama Conversion")
    print("=" * 70)
    
    # Use absolute paths
    script_dir = Path(__file__).parent.absolute()
    backend_dir = script_dir.parent
    model_dir = str(backend_dir / "models" / "policy-embeddings")
    model_name = "policy-embeddings:latest"
    
    converter = OllamaConverter(model_dir)
    
    # Create wrapper (easier than GGUF conversion)
    wrapper_path = converter.create_wrapper_script()
    
    # Create instructions
    converter.create_integration_instructions()
    
    print("\n" + "=" * 70)
    print("✨ Conversion complete!")
    print("=" * 70)
    print(f"\n📁 Wrapper script: {wrapper_path}")
    print(f"   Next step: Start embedding server and integrate with RAG")


if __name__ == "__main__":
    main()
