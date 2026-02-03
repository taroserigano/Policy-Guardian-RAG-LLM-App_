"""
Quick Test Validation Script
Validates test files are properly structured
"""
import os
import sys
from pathlib import Path

def check_file(filepath, file_type="test"):
    """Check if a file exists and is valid."""
    if not filepath.exists():
        return False, f"File not found: {filepath}"
    
    if filepath.stat().st_size == 0:
        return False, f"File is empty: {filepath}"
    
    # Basic syntax check
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if file_type == "test" and "def test_" not in content:
                return False, f"No test functions found in: {filepath.name}"
            if file_type == "test" and "import" not in content:
                return False, f"No imports found in: {filepath.name}"
    except Exception as e:
        return False, f"Error reading {filepath.name}: {e}"
    
    return True, f"✓ {filepath.name}"


def main():
    """Main validation."""
    backend_tests = Path(__file__).parent
    project_root = backend_tests.parent.parent
    
    print("="*70)
    print("TEST VALIDATION REPORT")
    print("="*70)
    print()
    
    # Backend tests
    print("Backend Tests:")
    print("-" * 70)
    
    backend_test_files = [
        backend_tests / "test_simple_server.py",
        backend_tests / "test_llm_providers.py",
        backend_tests / "test_e2e_complete.py",
        backend_tests / "run_comprehensive_tests.py",
    ]
    
    backend_passed = 0
    backend_total = len(backend_test_files)
    
    for test_file in backend_test_files:
        is_runner = "run_" in test_file.name
        valid, message = check_file(test_file, "runner" if is_runner else "test")
        print(f"  {message}")
        if valid:
            backend_passed += 1
    
    print()
    
    # Frontend tests
    print("Frontend Tests:")
    print("-" * 70)
    
    frontend_tests = project_root / "frontend" / "src" / "tests"
    
    if not frontend_tests.exists():
        print("  ✗ Frontend tests directory not found")
        frontend_passed = 0
        frontend_total = 0
    else:
        frontend_test_files = [
            frontend_tests / "ChatBox.enhanced.test.jsx",
            frontend_tests / "api.client.test.jsx",
            frontend_tests / "ChatBox.test.jsx",
            frontend_tests / "FileDrop.test.jsx",
            frontend_tests / "setup.js",
        ]
        
        frontend_passed = 0
        frontend_total = len(frontend_test_files)
        
        for test_file in frontend_test_files:
            if test_file.exists():
                print(f"  ✓ {test_file.name}")
                frontend_passed += 1
            else:
                print(f"  ⚠ {test_file.name} (not found)")
    
    print()
    
    # Documentation
    print("Documentation:")
    print("-" * 70)
    
    docs = [
        project_root / "COMPREHENSIVE_TESTING_GUIDE.md",
    ]
    
    docs_passed = 0
    for doc in docs:
        if doc.exists():
            print(f"  ✓ {doc.name}")
            docs_passed += 1
        else:
            print(f"  ✗ {doc.name}")
    
    print()
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Backend Tests:  {backend_passed}/{backend_total} files valid")
    print(f"Frontend Tests: {frontend_passed}/{frontend_total} files found")
    print(f"Documentation:  {docs_passed}/{len(docs)} files present")
    print()
    
    total_passed = backend_passed + frontend_passed + docs_passed
    total_files = backend_total + frontend_total + len(docs)
    
    if total_passed == total_files:
        print("✓ ALL TEST FILES VALIDATED SUCCESSFULLY")
        print()
        print("To run tests:")
        print("  Backend:  python tests/run_comprehensive_tests.py --quick")
        print("  Frontend: cd ../frontend && npm run test")
        return 0
    else:
        print(f"⚠ {total_files - total_passed} file(s) missing or invalid")
        return 1


if __name__ == "__main__":
    sys.exit(main())
