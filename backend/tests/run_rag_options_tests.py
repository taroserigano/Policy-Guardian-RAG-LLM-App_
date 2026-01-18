"""
Comprehensive Test Runner for Advanced RAG Options
Runs unit, integration, and E2E tests with detailed reporting
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*70)
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    """Run all RAG options tests."""
    os.chdir(Path(__file__).parent.parent)
    
    print("\n" + "="*70)
    print("ADVANCED RAG OPTIONS - COMPREHENSIVE TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = {}
    
    # Test 1: Unit Tests
    print("\n" + "#"*70)
    print("# PHASE 1: UNIT TESTS")
    print("#"*70)
    
    unit_tests = [
        "tests/test_unit_rag_options.py::TestQueryExpansion",
        "tests/test_unit_rag_options.py::TestSimpleReranker",
        "tests/test_unit_rag_options.py::TestLLMReranker",
        "tests/test_unit_rag_options.py::TestHybridScoring",
        "tests/test_unit_rag_options.py::TestCitationClass",
        "tests/test_unit_rag_options.py::TestRAGOptionsType",
        "tests/test_unit_rag_options.py::TestRAGOptionsSchema",
    ]
    
    for test in unit_tests:
        test_name = test.split("::")[-1]
        success = run_command(
            [sys.executable, "-m", "pytest", test, "-v", "--tb=short"],
            f"Unit Test: {test_name}"
        )
        results[f"Unit: {test_name}"] = "✅ PASS" if success else "❌ FAIL"
    
    # Test 2: Integration Tests
    print("\n" + "#"*70)
    print("# PHASE 2: INTEGRATION TESTS")
    print("#"*70)
    
    integration_tests = [
        "tests/test_integration_rag_options.py::TestRetrievalWithOptions",
        "tests/test_integration_rag_options.py::TestMultiQueryRetrieval",
        "tests/test_integration_rag_options.py::TestRAGPipelineWithOptions",
        "tests/test_integration_rag_options.py::TestRAGErrorHandling",
    ]
    
    for test in integration_tests:
        test_name = test.split("::")[-1]
        success = run_command(
            [sys.executable, "-m", "pytest", test, "-v", "--tb=short", "-m", "integration or not integration"],
            f"Integration Test: {test_name}"
        )
        results[f"Integration: {test_name}"] = "✅ PASS" if success else "❌ FAIL"
    
    # Test 3: E2E Tests
    print("\n" + "#"*70)
    print("# PHASE 3: END-TO-END TESTS")
    print("#"*70)
    
    e2e_tests = [
        "tests/test_e2e_rag_options.py::TestChatStreamEndpoint",
        "tests/test_e2e_rag_options.py::TestChatEndpoint",
        "tests/test_e2e_rag_options.py::TestFullPipelineE2E",
        "tests/test_e2e_rag_options.py::TestResponseFormat",
        "tests/test_e2e_rag_options.py::TestErrorScenarios",
    ]
    
    for test in e2e_tests:
        test_name = test.split("::")[-1]
        success = run_command(
            [sys.executable, "-m", "pytest", test, "-v", "--tb=short"],
            f"E2E Test: {test_name}"
        )
        results[f"E2E: {test_name}"] = "✅ PASS" if success else "❌ FAIL"
    
    # Summary Report
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if "PASS" in v)
    failed = sum(1 for v in results.values() if "FAIL" in v)
    total = len(results)
    
    for test_name, status in results.items():
        print(f"  {status} {test_name}")
    
    print("\n" + "-"*70)
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print("="*70)
    
    # Return exit code
    return 0 if failed == 0 else 1


def run_quick_tests():
    """Run quick unit tests only."""
    os.chdir(Path(__file__).parent.parent)
    
    print("\n" + "="*70)
    print("QUICK TEST RUN - Unit Tests Only")
    print("="*70)
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_unit_rag_options.py",
        "-v", "--tb=short", "-x"  # Stop on first failure
    ])
    
    return result.returncode


def run_all_rag_tests():
    """Run all RAG-related tests in one go."""
    os.chdir(Path(__file__).parent.parent)
    
    print("\n" + "="*70)
    print("FULL RAG OPTIONS TEST SUITE")
    print("="*70)
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_unit_rag_options.py",
        "tests/test_integration_rag_options.py",
        "tests/test_e2e_rag_options.py",
        "-v", "--tb=short",
        "--ignore=tests/test_e2e_rag_options.py::TestPerformance"  # Skip slow tests
    ])
    
    return result.returncode


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run RAG Options Tests")
    parser.add_argument("--quick", action="store_true", help="Run quick unit tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests in one go")
    parser.add_argument("--full", action="store_true", help="Run full comprehensive suite with reporting")
    
    args = parser.parse_args()
    
    if args.quick:
        sys.exit(run_quick_tests())
    elif args.all:
        sys.exit(run_all_rag_tests())
    else:
        sys.exit(main())
