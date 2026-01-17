"""
Document Chunking Module
Handles splitting documents into optimal chunks for RAG
"""
from typing import List, Dict, Any, Optional
import re
from dataclasses import dataclass


@dataclass
class Chunk:
    """Represents a document chunk."""
    text: str
    index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]


class DocumentChunker:
    """
    Smart document chunking for RAG applications.
    Supports multiple chunking strategies optimized for policy documents.
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum chunk size (smaller chunks are merged)
            separators: List of separators to split on (in order of priority)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.separators = separators or [
            "\n\n\n",  # Triple newlines (major sections)
            "\n\n",    # Double newlines (paragraphs)
            "\n",      # Single newlines
            ". ",      # Sentences
            ", ",      # Clauses
            " ",       # Words
            ""         # Characters (last resort)
        ]
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Split text into chunks using recursive character splitting.
        
        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to chunks
        
        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        # Recursively split
        chunks_text = self._recursive_split(text, self.separators)
        
        # Merge small chunks and create Chunk objects
        chunks = []
        current_pos = 0
        
        for i, chunk_text in enumerate(chunks_text):
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue
            
            # Find position in original text
            start_pos = text.find(chunk_text, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(chunk_text)
            current_pos = end_pos
            
            chunk_metadata = {
                "chunk_index": i,
                "chunk_total": len(chunks_text),
                "start_char": start_pos,
                "end_char": end_pos
            }
            if metadata:
                chunk_metadata.update(metadata)
            
            chunks.append(Chunk(
                text=chunk_text,
                index=i,
                start_char=start_pos,
                end_char=end_pos,
                metadata=chunk_metadata
            ))
        
        # Renumber chunks
        for i, chunk in enumerate(chunks):
            chunk.index = i
            chunk.metadata["chunk_index"] = i
            chunk.metadata["chunk_total"] = len(chunks)
        
        return chunks
    
    def _recursive_split(
        self,
        text: str,
        separators: List[str]
    ) -> List[str]:
        """Recursively split text using separators."""
        if not text:
            return []
        
        # If text is small enough, return it
        if len(text) <= self.chunk_size:
            return [text]
        
        # Find the best separator that exists in the text
        separator = ""
        for sep in separators:
            if sep in text:
                separator = sep
                break
        
        # If no separator found (shouldn't happen with "" as last separator)
        if separator == "":
            # Split by character count
            return self._split_by_size(text)
        
        # Split by separator
        splits = text.split(separator)
        
        # Merge splits back together up to chunk_size
        chunks = []
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_length = len(split) + len(separator)
            
            if current_length + split_length > self.chunk_size and current_chunk:
                # Save current chunk and start new one
                chunk_text = separator.join(current_chunk)
                
                # If chunk is still too large, recursively split
                if len(chunk_text) > self.chunk_size:
                    # Use next separator level
                    next_separators = separators[separators.index(separator) + 1:] if separator in separators else [""]
                    chunks.extend(self._recursive_split(chunk_text, next_separators))
                else:
                    chunks.append(chunk_text)
                
                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    # Include last part of previous chunk for overlap
                    overlap_text = separator.join(current_chunk[-1:])
                    if len(overlap_text) <= self.chunk_overlap:
                        current_chunk = [overlap_text, split]
                        current_length = len(overlap_text) + split_length
                    else:
                        current_chunk = [split]
                        current_length = split_length
                else:
                    current_chunk = [split]
                    current_length = split_length
            else:
                current_chunk.append(split)
                current_length += split_length
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = separator.join(current_chunk)
            if len(chunk_text) > self.chunk_size:
                next_separators = separators[separators.index(separator) + 1:] if separator in separators else [""]
                chunks.extend(self._recursive_split(chunk_text, next_separators))
            else:
                chunks.append(chunk_text)
        
        return chunks
    
    def _split_by_size(self, text: str) -> List[str]:
        """Split text by character count with overlap."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at a word boundary
            if end < len(text):
                # Look for last space before end
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space
            
            chunks.append(text[start:end])
            start = end - self.chunk_overlap if self.chunk_overlap > 0 else end
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Normalize whitespace
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()


class PolicyDocumentChunker(DocumentChunker):
    """
    Specialized chunker for policy documents.
    Recognizes sections, headers, and structured content.
    """
    
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100
    ):
        # Policy documents benefit from larger chunks
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n\n",           # Major sections
                "\n\n",              # Paragraphs
                "\n",                # Lines
                ". ",                # Sentences
                "; ",                # Semi-colon separated
                ", ",                # Commas
                " ",                 # Words
            ]
        )
        
        # Patterns to identify section headers
        self.section_patterns = [
            r'^#+\s+',                    # Markdown headers
            r'^\d+\.\s+[A-Z]',            # Numbered sections "1. SECTION"
            r'^[A-Z][A-Z\s]+:',           # UPPERCASE HEADER:
            r'^[A-Z][A-Z\s]+$',           # UPPERCASE HEADER (whole line)
            r'^\*\*[^*]+\*\*:?',          # **Bold header**:
        ]
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Chunk policy document with section awareness.
        """
        if not text or not text.strip():
            return []
        
        text = self._clean_text(text)
        
        # Try to identify and preserve sections
        sections = self._identify_sections(text)
        
        all_chunks = []
        for section in sections:
            section_metadata = {**(metadata or {})}
            if section.get("header"):
                section_metadata["section"] = section["header"]
            
            # Chunk each section
            section_chunks = super().chunk_text(
                section["content"],
                section_metadata
            )
            all_chunks.extend(section_chunks)
        
        # Renumber all chunks
        for i, chunk in enumerate(all_chunks):
            chunk.index = i
            chunk.metadata["chunk_index"] = i
            chunk.metadata["chunk_total"] = len(all_chunks)
        
        return all_chunks
    
    def _identify_sections(self, text: str) -> List[Dict[str, str]]:
        """Identify sections in the document."""
        lines = text.split('\n')
        sections = []
        current_section = {"header": None, "content": []}
        
        for line in lines:
            is_header = False
            
            # Check if line matches any header pattern
            for pattern in self.section_patterns:
                if re.match(pattern, line.strip()):
                    is_header = True
                    break
            
            if is_header and current_section["content"]:
                # Save previous section
                sections.append({
                    "header": current_section["header"],
                    "content": '\n'.join(current_section["content"])
                })
                current_section = {"header": line.strip(), "content": []}
            elif is_header:
                current_section["header"] = line.strip()
            else:
                current_section["content"].append(line)
        
        # Add last section
        if current_section["content"]:
            sections.append({
                "header": current_section["header"],
                "content": '\n'.join(current_section["content"])
            })
        
        # If no sections found, return whole text as one section
        if not sections:
            sections = [{"header": None, "content": text}]
        
        return sections


# Convenience function
def chunk_document(
    text: str,
    filename: str,
    doc_id: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    is_policy: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience function to chunk a document and return list of dicts.
    
    Args:
        text: Document text content
        filename: Original filename
        doc_id: Document ID
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        is_policy: Use policy-aware chunking
    
    Returns:
        List of chunk dictionaries ready for vector store
    """
    metadata = {
        "doc_id": doc_id,
        "filename": filename
    }
    
    if is_policy:
        chunker = PolicyDocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    else:
        chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    chunks = chunker.chunk_text(text, metadata)
    
    return [
        {
            "text": chunk.text,
            "index": chunk.index,
            "metadata": chunk.metadata
        }
        for chunk in chunks
    ]


# Testing
if __name__ == "__main__":
    print("="*60)
    print("Document Chunker Test")
    print("="*60)
    
    test_document = """
EMPLOYEE LEAVE POLICY

1. ANNUAL LEAVE
All full-time employees are entitled to 20 days of paid annual leave per year.
Leave accrues at a rate of 1.67 days per month of service.
Unused leave may be carried over up to a maximum of 5 days.
Leave requests must be submitted at least 2 weeks in advance.

2. SICK LEAVE
Employees receive 10 days of paid sick leave per year.
A medical certificate is required for absences exceeding 3 consecutive days.
Sick leave does not carry over to the next year.
Unused sick leave is not paid out upon termination.

3. PARENTAL LEAVE
Maternity leave: 16 weeks (8 weeks at 100% pay, 8 weeks unpaid)
Paternity leave: 2 weeks at 100% pay
Adoption leave: Same as maternity leave
Leave must be taken within 12 months of birth or adoption.

4. REMOTE WORK POLICY
Hybrid work: Up to 2 days per week with manager approval
Full remote: 3+ days per week requires department head approval
Equipment provided: Laptop, monitor, keyboard, mouse
Home office stipend: $500 one-time, $75/month for internet
    """
    
    chunker = PolicyDocumentChunker(chunk_size=400, chunk_overlap=50)
    chunks = chunker.chunk_text(test_document, {"filename": "leave_policy.txt"})
    
    print(f"\nTotal chunks: {len(chunks)}\n")
    
    for chunk in chunks:
        print(f"Chunk {chunk.index + 1}/{len(chunks)}")
        print(f"  Section: {chunk.metadata.get('section', 'N/A')}")
        print(f"  Length: {len(chunk.text)} chars")
        print(f"  Preview: {chunk.text[:100]}...")
        print()
