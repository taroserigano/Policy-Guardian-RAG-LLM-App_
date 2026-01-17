"""
Comprehensive Test Runner
Runs all unit, integration, and e2e tests
"""
import sys
import os
from pathlib import Path
import subprocess

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def run_tests(test_file, test_name):
    """Run a test file and return success status"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Running: {test_name}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"{GREEN}[PASS] {test_name} completed successfully{RESET}")
            return True
        else:
            print(f"{RED}[FAIL] {test_name} failed with exit code {result.returncode}{RESET}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"{RED}[FAIL] {test_name} timed out after 300 seconds{RESET}")
        return False
    except Exception as e:
        print(f"{RED}[FAIL] {test_name} error: {e}{RESET}")
        return False


def main():
    """Run all test suites"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}COMPREHENSIVE TEST SUITE - AI RAG APPLICATION{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    # Get test directory
    tests_dir = Path(__file__).parent
    
    # Define test suites
    test_suites = [
        (tests_dir / "test_unit_llm.py", "Unit Tests - LLM Functions"),
        (tests_dir / "test_integration_api.py", "Integration Tests - API Endpoints"),
        (tests_dir / "test_e2e_workflows.py", "E2E Tests - Complete Workflows"),
    ]
    
    results = []
    
    # Run each test suite
    for test_file, test_name in test_suites:
        if test_file.exists():
            success = run_tests(str(test_file), test_name)
            results.append((test_name, success))
        else:
            print(f"{YELLOW}[SKIP] {test_name} - File not found: {test_file}{RESET}")
            results.append((test_name, None))
    
    # Summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    passed = sum(1 for _, success in results if success is True)
    failed = sum(1 for _, success in results if success is False)
    skipped = sum(1 for _, success in results if success is None)
    total = len(results)
    
    for test_name, success in results:
        if success is True:
            status = f"{GREEN}[PASS]{RESET}"
        elif success is False:
            status = f"{RED}[FAIL]{RESET}"
        else:
            status = f"{YELLOW}[SKIP]{RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    if failed == 0 and passed > 0:
        print(f"{GREEN}[SUCCESS] ALL TESTS PASSED: {passed}/{total - skipped}{RESET}")
    else:
        print(f"{YELLOW}Results: {passed} passed, {failed} failed, {skipped} skipped{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
