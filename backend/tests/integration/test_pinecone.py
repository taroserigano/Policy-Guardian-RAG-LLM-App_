"""
Test Pinecone vector store connection
"""
import os
from dotenv import load_dotenv
from pathlib import Path
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "contract-policy-rag")

if not API_KEY:
    print("❌ PINECONE_API_KEY not found in environment variables")
    exit(1)

print(f"🔗 Connecting to Pinecone...")
print(f"   Index: {INDEX_NAME}")

try:
    pc = Pinecone(api_key=API_KEY)
    
    # List existing indexes
    indexes = pc.list_indexes()
    print(f"✅ Pinecone connected successfully!")
    print(f"   Found {len(indexes)} indexes")
    
    # Check if our index exists
    index_exists = any(idx.name == INDEX_NAME for idx in indexes)
    
    if index_exists:
        print(f"✅ Index '{INDEX_NAME}' already exists")
        index = pc.Index(INDEX_NAME)
        stats = index.describe_index_stats()
        print(f"   Dimensions: {stats.get('dimension', 'N/A')}")
        print(f"   Total vectors: {stats.get('total_vector_count', 0)}")
    else:
        print(f"⚠️  Index '{INDEX_NAME}' does not exist")
        print(f"   Creating index with 768 dimensions (sentence-transformers)...")
        
        pc.create_index(
            name=INDEX_NAME,
            dimension=768,  # sentence-transformers/all-mpnet-base-v2
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        print(f"✅ Index created successfully!")
        
except Exception as e:
    print(f"❌ Pinecone connection failed:")
    print(f"   Error: {str(e)}")
    exit(1)
