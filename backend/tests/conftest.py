"""
Pytest configuration and shared fixtures for backend tests.
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def client():
    """Create test client for enhanced_server_v2."""
    from starlette.testclient import TestClient
    from enhanced_server_v2 import app
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def simple_client():
    """Create test client for simple_server."""
    from starlette.testclient import TestClient
    from simple_server import app
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_txt_file():
    """Create a sample text file for testing."""
    from io import BytesIO
    content = b"This is a test document for upload testing."
    return ("test.txt", BytesIO(content), "text/plain")


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF-like file for testing."""
    from io import BytesIO
    # Minimal PDF content
    content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    return ("test.pdf", BytesIO(content), "application/pdf")


@pytest.fixture
def test_user_id():
    """Provide a consistent test user ID."""
    return "test-user-12345"
