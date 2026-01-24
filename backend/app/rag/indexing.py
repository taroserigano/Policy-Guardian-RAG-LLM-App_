"""
Document indexing pipeline: extract text, chunk, embed, and store in Pinecone.
Handles PDF and TXT files.
"""
from typing import List, Dict, Any, BinaryIO
import io
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec
import pypdf

from app.core.config import get_settings
from app.core.logging import get_logger
from app.rag.embeddings import get_default_embeddings

settings = get_settings()
logger = get_logger(__name__)

# Initialize Pinecone client
pc = Pinecone(api_key=settings.pinecone_api_key)


def ensure_index_exists() -> None:
    """
    Create Pinecone index if it doesn't exist.
    Uses serverless spec for cost efficiency.
    """
    index_name = settings.pinecone_index_name
    
    if index_name not in pc.list_indexes().names():
        logger.info(f"Creating Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=settings.embed_dim,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.pinecone_cloud,
                region=settings.pinecone_region
            )
        )
        logger.info(f"Index {index_name} created successfully")
    else:
        logger.info(f"Index {index_name} already exists")


def get_pinecone_index():
    """Get Pinecone index instance."""
    ensure_index_exists()
    return pc.Index(settings.pinecone_index_name)


def extract_text_from_pdf(file_path: str) -> tuple[str, List[Dict[str, Any]]]:
    """
    Extract text from PDF file with page numbers.
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        Tuple of (full_text, pages_metadata)
        pages_metadata contains page numbers and text per page
    """
    try:
        # Use pypdf directly instead of langchain loader
        full_text = ""
        pages_metadata = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            
            for i, page in enumerate(pdf_reader.pages):
                page_num = i + 1
                page_text = page.extract_text()
                full_text += page_text + "\n\n"
                pages_metadata.append({
                    "page_number": page_num,
                    "text": page_text
                })
        
        return full_text, pages_metadata
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from TXT file.
    
    Args:
        file_path: Path to TXT file
    
    Returns:
        Text content
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    except Exception as e:
        logger.error(f"Error extracting text from TXT: {e}")
        raise


def chunk_text(text: str) -> List[str]:
    """
    Split text into chunks using RecursiveCharacterTextSplitter.
    
    Args:
        text: Full document text
    
    Returns:
        List of text chunks
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_text(text)
    logger.info(f"Split text into {len(chunks)} chunks")
    return chunks


def index_document(
    doc_id: str,
    filename: str,
    file_path: str,
    content_type: str
) -> Dict[str, Any]:
    """
    Complete indexing pipeline: extract, chunk, embed, and upsert to Pinecone.
    
    Args:
        doc_id: Unique document ID (UUID)
        filename: Original filename
        file_path: Path to file on disk
        content_type: MIME type (application/pdf or text/plain)
    
    Returns:
        Dictionary with preview_text and chunk_count
    """
    logger.info(f"Starting indexing for document: {filename}")
    
    # Step 1: Extract text
    if content_type == "application/pdf":
        full_text, pages_metadata = extract_text_from_pdf(file_path)
        page_mapping = {i: meta["page_number"] for i, meta in enumerate(pages_metadata)}
    else:
        full_text = extract_text_from_txt(file_path)
        page_mapping = None
    
    # Step 2: Chunk text
    chunks = chunk_text(full_text)
    
    # Step 3: Generate embeddings
    logger.info(f"Generating embeddings for {len(chunks)} chunks...")
    embeddings = get_default_embeddings().embed_documents(chunks)
    
    # Step 4: Prepare vectors for Pinecone
    vectors = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        vector_id = f"{doc_id}:{i}"
        
        # Build metadata
        metadata = {
            "doc_id": doc_id,
            "filename": filename,
            "source_type": content_type,
            "chunk_index": i,
            "text": chunk  # Store text in metadata for retrieval
        }
        
        # Add page number for PDFs
        if page_mapping:
            # Estimate which page this chunk came from
            # Simple heuristic: divide by number of chunks
            estimated_page = min(
                max(1, int((i / len(chunks)) * len(page_mapping)) + 1),
                len(page_mapping)
            )
            metadata["page_number"] = estimated_page
        
        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": metadata
        })
    
    # Step 5: Upsert to Pinecone
    logger.info(f"Upserting {len(vectors)} vectors to Pinecone...")
    index = get_pinecone_index()
    index.upsert(vectors=vectors, namespace="")
    
    logger.info(f"Successfully indexed document {filename}")
    
    # Return preview text (first 500 chars)
    preview_text = full_text[:500] if len(full_text) > 500 else full_text
    
    return {
        "preview_text": preview_text,
        "chunk_count": len(chunks)
    }


def delete_document_from_index(doc_id: str) -> None:
    """
    Delete all vectors for a document from Pinecone.
    
    Args:
        doc_id: Document UUID
    """
    try:
        index = get_pinecone_index()
        
        # Query to get all vector IDs for this document
        # Pinecone doesn't support prefix deletion directly, so we fetch and delete
        logger.info(f"Deleting vectors for document: {doc_id}")
        
        # Use delete with filter
        index.delete(filter={"doc_id": {"$eq": doc_id}})
        
        logger.info(f"Deleted all vectors for document {doc_id}")
    
    except Exception as e:
        logger.error(f"Error deleting document from index: {e}")
        raise

