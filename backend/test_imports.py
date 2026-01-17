"""Test module imports"""
import sys
sys.path.insert(0, '.')

print("Testing imports...")

try:
    from app.rag.vector_store import get_vector_store
    print("  vector_store OK")
except Exception as e:
    print(f"  vector_store FAILED: {e}")

try:
    from app.rag.retriever import get_retriever
    print("  retriever OK")
except Exception as e:
    print(f"  retriever FAILED: {e}")

try:
    from app.db.database import get_database
    print("  database OK")
except Exception as e:
    print(f"  database FAILED: {e}")

print("\nAll imports complete!")
