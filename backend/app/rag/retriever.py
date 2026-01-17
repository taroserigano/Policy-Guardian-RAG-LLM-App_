"""
RAG Retrieval Module
Handles semantic search and context building for RAG pipeline
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .vector_store import VectorStore, get_vector_store
from .chunking import chunk_document, PolicyDocumentChunker


@dataclass
class RetrievalResult:
    """Single retrieval result."""
    text: str
    doc_id: str
    filename: str
    chunk_index: int
    score: float
    section: Optional[str] = None


class RAGRetriever:
    """
    Semantic search retriever for RAG applications.
    Handles document indexing and query retrieval.
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        persist_directory: str = "./data/chroma_db"
    ):
        """
        Initialize retriever.
        
        Args:
            vector_store: Optional existing vector store
            persist_directory: Directory for vector store persistence
        """
        self.vector_store = vector_store or get_vector_store(
            persist_directory=persist_directory
        )
    
    def index_document(
        self,
        doc_id: str,
        content: str,
        filename: str,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Index a document for retrieval.
        
        Args:
            doc_id: Unique document identifier
            content: Document text content
            filename: Original filename
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            additional_metadata: Extra metadata to store
        
        Returns:
            Number of chunks indexed
        """
        # Chunk the document
        chunks = chunk_document(
            text=content,
            filename=filename,
            doc_id=doc_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            is_policy=True
        )
        
        if not chunks:
            print(f"[WARNING] No chunks generated for document: {filename}")
            return 0
        
        # Prepare metadata
        metadata = {
            "filename": filename,
            "doc_id": doc_id
        }
        if additional_metadata:
            metadata.update(additional_metadata)
        
        # Extract just the text for indexing
        chunk_texts = [c["text"] for c in chunks]
        
        # Add to vector store
        num_chunks = self.vector_store.add_document(
            doc_id=doc_id,
            chunks=chunk_texts,
            metadata=metadata
        )
        
        print(f"[OK] Indexed document '{filename}': {num_chunks} chunks")
        return num_chunks
    
    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filter_doc_ids: Optional[List[str]] = None,
        min_score: float = 0.3
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant document chunks for a query.
        
        Args:
            query: Search query
            n_results: Maximum results to return
            filter_doc_ids: Optional document IDs to filter by
            min_score: Minimum similarity score
        
        Returns:
            List of RetrievalResult objects
        """
        # Search vector store
        results = self.vector_store.search(
            query=query,
            n_results=n_results,
            filter_doc_ids=filter_doc_ids,
            min_score=min_score
        )
        
        # Convert to RetrievalResult objects
        retrieval_results = []
        for r in results:
            metadata = r.get("metadata", {})
            retrieval_results.append(RetrievalResult(
                text=r["text"],
                doc_id=metadata.get("doc_id", "unknown"),
                filename=metadata.get("filename", "unknown"),
                chunk_index=metadata.get("chunk_index", 0),
                score=r["score"],
                section=metadata.get("section")
            ))
        
        return retrieval_results
    
    def build_context(
        self,
        query: str,
        n_results: int = 5,
        filter_doc_ids: Optional[List[str]] = None,
        max_context_length: int = 4000
    ) -> Dict[str, Any]:
        """
        Build context for LLM from retrieved chunks.
        
        Args:
            query: Search query
            n_results: Maximum chunks to retrieve
            filter_doc_ids: Optional document IDs to filter by
            max_context_length: Maximum context length in characters
        
        Returns:
            Dictionary with context string and citations
        """
        # Retrieve relevant chunks
        results = self.retrieve(
            query=query,
            n_results=n_results,
            filter_doc_ids=filter_doc_ids
        )
        
        if not results:
            return {
                "context": "",
                "citations": [],
                "num_chunks": 0
            }
        
        # Build context string
        context_parts = []
        citations = []
        total_length = 0
        
        for i, result in enumerate(results):
            # Format chunk for context
            chunk_header = f"[Source: {result.filename}"
            if result.section:
                chunk_header += f" - {result.section}"
            chunk_header += f" (Relevance: {result.score:.0%})]"
            
            chunk_text = f"{chunk_header}\n{result.text}"
            
            # Check if adding this chunk exceeds max length
            if total_length + len(chunk_text) > max_context_length:
                break
            
            context_parts.append(chunk_text)
            total_length += len(chunk_text)
            
            # Add citation
            citations.append({
                "doc_id": result.doc_id,
                "filename": result.filename,
                "chunk_index": result.chunk_index,
                "score": result.score,
                "text": result.text[:200] + "..." if len(result.text) > 200 else result.text,
                "section": result.section
            })
        
        context = "\n\n---\n\n".join(context_parts)
        
        return {
            "context": context,
            "citations": citations,
            "num_chunks": len(context_parts)
        }
    
    def delete_document(self, doc_id: str) -> int:
        """Delete a document from the index."""
        return self.vector_store.delete_document(doc_id)
    
    def get_indexed_documents(self) -> List[str]:
        """Get list of indexed document IDs."""
        return self.vector_store.get_unique_documents()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        return {
            "total_chunks": self.vector_store.get_document_count(),
            "unique_documents": len(self.get_indexed_documents()),
            "document_ids": self.get_indexed_documents()
        }


# Singleton instance
_retriever_instance: Optional[RAGRetriever] = None


def get_retriever(persist_directory: str = "./data/chroma_db") -> RAGRetriever:
    """Get or create the global retriever instance."""
    global _retriever_instance
    
    if _retriever_instance is None:
        _retriever_instance = RAGRetriever(persist_directory=persist_directory)
    
    return _retriever_instance


# Testing
if __name__ == "__main__":
    print("="*60)
    print("RAG Retriever Test")
    print("="*60)
    
    # Initialize retriever
    retriever = get_retriever(persist_directory="./data/test_retriever")
    
    # Sample documents
    documents = [
        {
            "id": "leave-policy",
            "filename": "employee_leave_policy.txt",
            "content": """
EMPLOYEE LEAVE POLICY

1. ANNUAL LEAVE
All full-time employees are entitled to 20 days of paid annual leave per year.
Leave accrues at a rate of 1.67 days per month of service.
Unused leave may be carried over up to a maximum of 5 days.
Leave requests must be submitted at least 2 weeks in advance through the HR portal.

2. SICK LEAVE
Employees receive 10 days of paid sick leave per year.
A medical certificate is required for absences exceeding 3 consecutive days.
Sick leave does not carry over to the next year.

3. PARENTAL LEAVE
Maternity leave: 16 weeks (8 weeks at 100% pay, 8 weeks unpaid)
Paternity leave: 2 weeks at 100% pay
            """
        },
        {
            "id": "remote-work",
            "filename": "remote_work_policy.txt",
            "content": """
REMOTE WORK POLICY

1. ELIGIBILITY
Employees must complete 6 months of service before requesting remote work.
Position must be suitable for remote execution.
Manager approval required for all remote work arrangements.

2. HYBRID WORK
Up to 2 days per week remote with manager approval.
Core hours: 9 AM to 4 PM local time.
Must be available for team meetings and collaboration.

3. EQUIPMENT
Company provides: Laptop, monitor, keyboard, mouse, headset.
Home office stipend: $500 one-time setup allowance.
Monthly internet allowance: $75.
            """
        }
    ]
    
    # Index documents
    print("\nIndexing documents...")
    for doc in documents:
        retriever.index_document(
            doc_id=doc["id"],
            content=doc["content"],
            filename=doc["filename"]
        )
    
    # Test queries
    test_queries = [
        "How many vacation days do I get?",
        "Can I work from home?",
        "What is the maternity leave policy?",
        "Do I need a doctor's note for sick leave?"
    ]
    
    print("\n" + "="*60)
    print("Testing Queries")
    print("="*60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        context_data = retriever.build_context(query, n_results=2)
        
        print(f"Found {context_data['num_chunks']} relevant chunks:")
        for citation in context_data['citations']:
            print(f"  • {citation['filename']} (score: {citation['score']:.2%})")
            print(f"    {citation['text'][:100]}...")
    
    # Stats
    print("\n" + "="*60)
    print("Retriever Stats")
    print("="*60)
    stats = retriever.get_stats()
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Unique documents: {stats['unique_documents']}")
