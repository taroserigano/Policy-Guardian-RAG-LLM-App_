"""
Test utility functions and helpers.
"""
import pytest
from app.api.routes_docs import sanitize_filename


class TestFilenameUtils:
    """Test filename sanitization."""
    
    def test_sanitize_normal_filename(self):
        """Test sanitizing a normal filename."""
        result = sanitize_filename("document.pdf")
        assert result == "document.pdf"
    
    def test_sanitize_filename_with_path(self):
        """Test removing path traversal attempts."""
        result = sanitize_filename("../../etc/passwd")
        assert result == "etcpasswd"
        assert ".." not in result
        assert "/" not in result
    
    def test_sanitize_filename_with_spaces(self):
        """Test handling spaces."""
        result = sanitize_filename("my document.pdf")
        assert result == "my document.pdf"
    
    def test_sanitize_filename_with_special_chars(self):
        """Test removing special characters."""
        result = sanitize_filename("file@#$%^&*.pdf")
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result
    
    def test_sanitize_filename_windows_path(self):
        """Test removing Windows path separators."""
        result = sanitize_filename("C:\\Users\\test\\file.pdf")
        assert "\\" not in result
        assert ":" not in result
    
    def test_sanitize_empty_filename(self):
        """Test handling empty filename."""
        result = sanitize_filename("")
        assert result == ""
    
    def test_sanitize_filename_preserves_extension(self):
        """Test that file extension is preserved."""
        result = sanitize_filename("my-file_name.PDF")
        assert result.endswith(".PDF")
        assert "-" in result
        assert "_" in result
