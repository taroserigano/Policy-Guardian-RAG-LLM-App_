"""
System Validation Script
Checks all components of the Policy RAG application are working correctly.
"""

import sys
import os
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(title):
    print(f"\n{BLUE}{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}{RESET}\n")

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠️  {message}{RESET}")

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print_success(f"{description}: {filepath}")
        return True
    else:
        print_error(f"{description} not found: {filepath}")
        return False

def check_python_modules():
    """Check if required Python modules are installed."""
    print_header("Checking Python Dependencies")
    
    required_modules = [
        ('fastapi', 'FastAPI web framework'),
        ('sqlalchemy', 'Database ORM'),
        ('pydantic', 'Data validation'),
        ('pinecone', 'Vector database client'),
        ('langchain', 'LLM framework'),
        ('langgraph', 'RAG workflow'),
        ('pypdf', 'PDF processing'),
        ('pytest', 'Testing framework'),
    ]
    
    all_installed = True
    for module, description in required_modules:
        try:
            __import__(module)
            print_success(f"{description} ({module})")
        except ImportError:
            print_error(f"{description} ({module}) - Not installed")
            all_installed = False
    
    return all_installed

def check_backend_structure():
    """Check backend file structure."""
    print_header("Checking Backend Structure")
    
    backend_files = [
        ('backend/app/main.py', 'Main FastAPI app'),
        ('backend/app/core/config.py', 'Configuration'),
        ('backend/app/core/logging.py', 'Logging setup'),
        ('backend/app/db/models.py', 'Database models'),
        ('backend/app/db/session.py', 'Database session'),
        ('backend/app/rag/embeddings.py', 'Embedding handlers'),
        ('backend/app/rag/llms.py', 'LLM providers'),
        ('backend/app/rag/indexing.py', 'Document indexing'),
        ('backend/app/rag/retrieval.py', 'RAG retrieval'),
        ('backend/app/rag/graph.py', 'LangGraph workflow'),
        ('backend/app/api/routes_docs.py', 'Document routes'),
        ('backend/app/api/routes_chat.py', 'Chat routes'),
        ('backend/app/schemas.py', 'Pydantic schemas'),
        ('backend/requirements.txt', 'Python dependencies'),
        ('backend/Dockerfile', 'Docker configuration'),
    ]
    
    all_exist = True
    for filepath, description in backend_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_frontend_structure():
    """Check frontend file structure."""
    print_header("Checking Frontend Structure")
    
    frontend_files = [
        ('frontend/src/App.jsx', 'Main React app'),
        ('frontend/src/main.jsx', 'Entry point'),
        ('frontend/src/components/Layout.jsx', 'Layout component'),
        ('frontend/src/components/FileDrop.jsx', 'File upload component'),
        ('frontend/src/components/ModelPicker.jsx', 'Model selector'),
        ('frontend/src/components/MessageList.jsx', 'Chat messages'),
        ('frontend/src/components/ChatBox.jsx', 'Message input'),
        ('frontend/src/components/DocumentList.jsx', 'Document list'),
        ('frontend/src/components/CitationsList.jsx', 'Citations display'),
        ('frontend/src/pages/UploadPage.jsx', 'Upload page'),
        ('frontend/src/pages/ChatPage.jsx', 'Chat page'),
        ('frontend/src/api/client.js', 'API client'),
        ('frontend/src/hooks/useApi.js', 'React Query hooks'),
        ('frontend/package.json', 'Node dependencies'),
        ('frontend/Dockerfile', 'Docker configuration'),
        ('frontend/vite.config.js', 'Vite configuration'),
        ('frontend/tailwind.config.js', 'Tailwind configuration'),
    ]
    
    all_exist = True
    for filepath, description in frontend_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_test_structure():
    """Check test file structure."""
    print_header("Checking Test Structure")
    
    test_files = [
        ('backend/tests/run_tests.py', 'Unit test runner'),
        ('backend/tests/integration_test.py', 'Integration tests'),
        ('frontend/src/tests/setup.js', 'Test setup'),
        ('frontend/src/tests/FileDrop.test.jsx', 'FileDrop tests'),
        ('frontend/src/tests/ModelPicker.test.jsx', 'ModelPicker tests'),
        ('frontend/src/tests/MessageList.test.jsx', 'MessageList tests'),
        ('frontend/src/tests/ChatBox.test.jsx', 'ChatBox tests'),
        ('frontend/vitest.config.js', 'Vitest configuration'),
    ]
    
    all_exist = True
    for filepath, description in test_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_config_files():
    """Check configuration files."""
    print_header("Checking Configuration Files")
    
    config_files = [
        ('docker-compose.yml', 'Docker Compose'),
        ('backend/.env.example', 'Backend env template'),
        ('frontend/.env.example', 'Frontend env template'),
        ('.gitignore', 'Git ignore rules'),
        ('README.md', 'Documentation'),
        ('TESTING.md', 'Testing guide'),
    ]
    
    all_exist = True
    for filepath, description in config_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_env_configuration():
    """Check environment configuration."""
    print_header("Checking Environment Configuration")
    
    backend_env = 'backend/.env'
    if os.path.exists(backend_env):
        print_success(f"Backend .env file exists")
        
        # Check for required variables
        with open(backend_env, 'r') as f:
            env_content = f.read()
            
        required_vars = [
            'DATABASE_URL',
            'PINECONE_API_KEY',
            'OLLAMA_BASE_URL',
        ]
        
        all_present = True
        for var in required_vars:
            if var in env_content:
                print_success(f"  {var} configured")
            else:
                print_warning(f"  {var} not found (optional for some setups)")
        
        return True
    else:
        print_warning("Backend .env not found - copy from .env.example")
        return False

def run_unit_tests():
    """Run unit tests."""
    print_header("Running Unit Tests")
    
    test_script = 'backend/tests/run_tests.py'
    if os.path.exists(test_script):
        print("Executing unit tests...")
        result = os.system(f'python {test_script}')
        if result == 0:
            print_success("Unit tests passed")
            return True
        else:
            print_error("Unit tests failed")
            return False
    else:
        print_error("Test script not found")
        return False

def count_lines_of_code():
    """Count lines of code in the project."""
    print_header("Code Statistics")
    
    def count_lines(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except:
            return 0
    
    # Backend Python files
    backend_lines = 0
    backend_files = 0
    for root, dirs, files in os.walk('backend/app'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                backend_lines += count_lines(filepath)
                backend_files += 1
    
    # Frontend JavaScript files
    frontend_lines = 0
    frontend_files = 0
    for root, dirs, files in os.walk('frontend/src'):
        for file in files:
            if file.endswith(('.jsx', '.js')):
                filepath = os.path.join(root, file)
                frontend_lines += count_lines(filepath)
                frontend_files += 1
    
    # Test files
    test_lines = 0
    test_files = 0
    for root, dirs, files in os.walk('backend/tests'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                test_lines += count_lines(filepath)
                test_files += 1
    for root, dirs, files in os.walk('frontend/src/tests'):
        for file in files:
            if file.endswith(('.jsx', '.js')):
                filepath = os.path.join(root, file)
                test_lines += count_lines(filepath)
                test_files += 1
    
    print(f"Backend:  {backend_files:3d} files, {backend_lines:5d} lines")
    print(f"Frontend: {frontend_files:3d} files, {frontend_lines:5d} lines")
    print(f"Tests:    {test_files:3d} files, {test_lines:5d} lines")
    print(f"Total:    {backend_files + frontend_files + test_files:3d} files, {backend_lines + frontend_lines + test_lines:5d} lines")

def main():
    """Main validation function."""
    print(f"\n{BLUE}{'='*70}")
    print("  POLICY RAG APPLICATION - SYSTEM VALIDATION")
    print(f"{'='*70}{RESET}")
    
    results = {
        'Python Dependencies': check_python_modules(),
        'Backend Structure': check_backend_structure(),
        'Frontend Structure': check_frontend_structure(),
        'Test Structure': check_test_structure(),
        'Configuration Files': check_config_files(),
        'Environment Setup': check_env_configuration(),
    }
    
    # Count code
    count_lines_of_code()
    
    # Run tests
    results['Unit Tests'] = run_unit_tests()
    
    # Summary
    print_header("Validation Summary")
    
    all_passed = True
    for check, passed in results.items():
        if passed:
            print_success(f"{check}")
        else:
            print_error(f"{check}")
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print_success("🎉 All validation checks passed!")
        print_success("   Your Policy RAG application is ready to use!")
    else:
        print_warning("⚠️  Some checks failed - review the output above")
        print_warning("   Fix the issues and run validation again")
    print("="*70 + "\n")
    
    # Next steps
    if all_passed:
        print(f"{BLUE}Next Steps:{RESET}")
        print("1. Start services:  docker-compose up -d")
        print("2. Open frontend:   http://localhost:5173")
        print("3. Access backend:  http://localhost:8000")
        print("4. View docs:       http://localhost:8000/docs")
        print("5. Run integration: python backend/tests/integration_test.py")
        print()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
