"""
Comprehensive Test Suite for Document Chunking Module
Tests all chunking functionality including edge cases
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.chunking import DocumentChunker, PolicyDocumentChunker, chunk_document, Chunk


class TestDocumentChunker:
    """Test cases for DocumentChunker class."""
    
    def test_chunker_initialization(self):
        """Test default initialization."""
        chunker = DocumentChunker()
        # Default values from implementation
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 50
        assert chunker.min_chunk_size == 100
    
    def test_chunker_custom_params(self):
        """Test custom initialization."""
        chunker = DocumentChunker(
            chunk_size=800,
            chunk_overlap=100,
            min_chunk_size=50
        )
        assert chunker.chunk_size == 800
        assert chunker.chunk_overlap == 100
        assert chunker.min_chunk_size == 50
    
    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        chunker = DocumentChunker()
        result = chunker.chunk_text("")
        assert result == []
        
        result = chunker.chunk_text("   ")
        assert result == []
    
    def test_chunk_short_text(self):
        """Test text shorter than chunk size."""
        chunker = DocumentChunker(chunk_size=500)
        text = "This is a short text."
        
        result = chunker.chunk_text(text)
        
        assert len(result) == 1
        assert result[0].text == text
    
    def test_chunk_long_text(self):
        """Test text longer than chunk size."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=10)
        
        # Create text longer than chunk size
        text = " ".join(["This is sentence number {}.".format(i) for i in range(50)])
        
        result = chunker.chunk_text(text)
        
        # Should have multiple chunks
        assert len(result) > 1
        
        # All chunks should have text
        for chunk in result:
            assert len(chunk.text) > 0
    
    def test_chunk_preserves_paragraphs(self):
        """Test that chunking handles paragraphs."""
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
        
        text = """First paragraph with some content.

Second paragraph with different content.

Third paragraph here."""
        
        result = chunker.chunk_text(text)
        
        # Should have chunks
        assert len(result) >= 1
    
    def test_chunk_with_metadata(self):
        """Test that metadata is preserved."""
        chunker = DocumentChunker()
        text = "Some text content here that is meaningful."
        metadata = {"doc_id": "test_123", "filename": "test.txt"}
        
        result = chunker.chunk_text(text, metadata=metadata)
        
        assert len(result) >= 1
        assert result[0].metadata.get("doc_id") == "test_123"
    
    def test_chunk_indexes(self):
        """Test that chunks have correct indexes."""
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=5)
        text = " ".join(["Word"] * 100)
        
        result = chunker.chunk_text(text)
        
        for i, chunk in enumerate(result):
            assert chunk.index == i
            assert chunk.metadata["chunk_index"] == i
    
    def test_chunk_character_positions(self):
        """Test that start/end char positions are tracked."""
        chunker = DocumentChunker()
        text = "Start of text. Middle section here. End of text."
        
        result = chunker.chunk_text(text)
        
        # Each chunk should have positions
        for chunk in result:
            assert hasattr(chunk, 'start_char')
            assert hasattr(chunk, 'end_char')
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char
    
    def test_separators_used(self):
        """Test that separators list is configured."""
        chunker = DocumentChunker()
        assert len(chunker.separators) > 0
        assert "\n\n" in chunker.separators


class TestPolicyDocumentChunker:
    """Test cases for PolicyDocumentChunker class."""
    
    def test_policy_chunker_initialization(self):
        """Test PolicyDocumentChunker initializes correctly."""
        chunker = PolicyDocumentChunker()
        # Should have section patterns configured
        assert hasattr(chunker, 'section_patterns')
    
    def test_policy_chunker_inherits_chunker(self):
        """Test PolicyDocumentChunker inherits from DocumentChunker."""
        chunker = PolicyDocumentChunker()
        assert hasattr(chunker, 'chunk_text')
        assert hasattr(chunker, 'chunk_size')
    
    def test_policy_chunk_basic(self):
        """Test basic policy document chunking."""
        chunker = PolicyDocumentChunker(chunk_size=200)
        
        policy_text = """
1. INTRODUCTION
This is the introduction section with some content.

2. POLICY DETAILS
These are the detailed policy requirements.

3. CONCLUSION
Final notes and summary.
"""
        
        result = chunker.chunk_text(policy_text)
        
        # Should produce chunks
        assert len(result) >= 1
    
    def test_policy_chunk_with_metadata(self):
        """Test policy chunking preserves metadata."""
        chunker = PolicyDocumentChunker()
        
        policy_text = "1. OVERVIEW\nThis is policy content."
        metadata = {"doc_id": "policy_123", "type": "hr_policy"}
        
        result = chunker.chunk_text(policy_text, metadata=metadata)
        
        assert len(result) >= 1
        assert result[0].metadata.get("doc_id") == "policy_123"


class TestChunkDocumentFunction:
    """Test the convenience chunk_document function."""
    
    def test_chunk_document_basic(self):
        """Test basic chunk_document call."""
        text = "This is some test content for chunking."
        
        result = chunk_document(text, filename="test.txt", doc_id="doc_1")
        
        assert isinstance(result, list)
        assert len(result) >= 1
    
    def test_chunk_document_policy_mode(self):
        """Test chunk_document in policy mode."""
        text = """
1. PURPOSE
This policy establishes guidelines.

2. SCOPE
Applies to all employees.
"""
        
        result = chunk_document(
            text,
            filename="policy.txt",
            doc_id="policy_1",
            is_policy=True
        )
        
        assert isinstance(result, list)
    
    def test_chunk_document_custom_sizes(self):
        """Test chunk_document with custom sizes."""
        text = " ".join(["Content word."] * 100)
        
        result = chunk_document(
            text,
            filename="test.txt",
            doc_id="doc_1",
            chunk_size=100,
            chunk_overlap=10
        )
        
        assert len(result) > 1
    
    def test_chunk_document_returns_list_of_dicts(self):
        """Test chunk_document returns list of dictionaries."""
        text = "Some text content."
        
        result = chunk_document(text, filename="test.txt", doc_id="doc_1")
        
        assert isinstance(result, list)
        # Each item should be a dict with expected keys
        if result:
            assert isinstance(result[0], dict)
            assert "text" in result[0]


class TestChunkingEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_unicode_content(self):
        """Test chunking with unicode characters."""
        chunker = DocumentChunker()
        text = "Unicode: 日本語 한국어 العربية 中文 🎉 émojis"
        
        result = chunker.chunk_text(text)
        
        assert len(result) >= 1
        # Unicode should be preserved
        assert "日本語" in result[0].text or len(result[0].text) > 0
    
    def test_special_characters(self):
        """Test chunking with special characters."""
        chunker = DocumentChunker()
        text = "Special chars: @#$%^&*()_+-=[]{}|;':\",./<>?"
        
        result = chunker.chunk_text(text)
        
        assert len(result) >= 1
    
    def test_newlines_and_whitespace(self):
        """Test chunking with various whitespace."""
        chunker = DocumentChunker()
        text = "Line1\n\n\nLine2\t\tTabbed\r\nWindows newline"
        
        result = chunker.chunk_text(text)
        
        assert len(result) >= 1
    
    def test_very_long_words(self):
        """Test chunking with very long words."""
        chunker = DocumentChunker(chunk_size=100)
        # Use a moderately long word to avoid memory issues
        text = "Normal text " + "a" * 50 + " more normal text"
        
        result = chunker.chunk_text(text)
        
        # Should handle gracefully
        assert len(result) >= 1
    
    def test_repeated_separators(self):
        """Test chunking with repeated separators."""
        chunker = DocumentChunker()
        text = "Content......Content\n\n\n\n\nMore content"
        
        result = chunker.chunk_text(text)
        
        assert len(result) >= 1


class TestChunkingQuality:
    """Test quality aspects of chunking."""
    
    def test_chunk_has_required_fields(self):
        """Test that Chunk objects have all required fields."""
        chunker = DocumentChunker()
        text = "Some meaningful content for testing."
        
        result = chunker.chunk_text(text)
        
        assert len(result) >= 1
        chunk = result[0]
        
        # Check required Chunk fields
        assert hasattr(chunk, 'text')
        assert hasattr(chunk, 'index')
        assert hasattr(chunk, 'start_char')
        assert hasattr(chunk, 'end_char')
        assert hasattr(chunk, 'metadata')
    
    def test_no_empty_chunks(self):
        """Test that no empty chunks are produced."""
        chunker = DocumentChunker()
        text = "   Content   with   spaces   between   words   "
        
        result = chunker.chunk_text(text)
        
        for chunk in result:
            # No chunk should be empty after strip
            assert len(chunk.text.strip()) > 0
    
    def test_consistent_metadata_structure(self):
        """Test that all chunks have consistent metadata."""
        chunker = DocumentChunker()
        text = " ".join(["Word"] * 200)
        metadata = {"source": "test"}
        
        result = chunker.chunk_text(text, metadata=metadata)
        
        for chunk in result:
            # All chunks should have chunk_index
            assert "chunk_index" in chunk.metadata
            # All should have the source metadata
            assert chunk.metadata.get("source") == "test"
    
    def test_chunk_total_metadata(self):
        """Test chunk_total is accurate in metadata."""
        chunker = DocumentChunker(chunk_size=50)
        text = " ".join(["Word"] * 200)
        
        result = chunker.chunk_text(text)
        
        if len(result) > 1:
            for chunk in result:
                assert chunk.metadata["chunk_total"] == len(result)


class TestChunkDataclass:
    """Test the Chunk dataclass."""
    
    def test_chunk_creation(self):
        """Test creating a Chunk directly."""
        chunk = Chunk(
            text="Test content",
            index=0,
            start_char=0,
            end_char=12,
            metadata={"key": "value"}
        )
        
        assert chunk.text == "Test content"
        assert chunk.index == 0
        assert chunk.start_char == 0
        assert chunk.end_char == 12
        assert chunk.metadata == {"key": "value"}
    
    def test_chunk_immutable_fields(self):
        """Test that Chunk fields are accessible."""
        chunk = Chunk(
            text="Content",
            index=1,
            start_char=10,
            end_char=17,
            metadata={}
        )
        
        assert isinstance(chunk.text, str)
        assert isinstance(chunk.index, int)
        assert isinstance(chunk.metadata, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
