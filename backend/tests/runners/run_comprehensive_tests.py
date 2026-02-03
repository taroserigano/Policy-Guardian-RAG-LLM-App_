"""
Comprehensive Test Runner
Runs all test suites and generates a detailed report
"""
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_section(text):
    """Print a formatted section."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{'-'*70}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{Colors.BOLD}{'-'*70}{Colors.ENDC}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_failure(text):
    """Print failure message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def run_command(cmd, description, cwd=None):
    """
    Run a command and capture output.
    
    Args:
        cmd: Command to run as list
        description: Description of what's being tested
        cwd: Working directory for command
    
    Returns:
        tuple: (success: bool, duration: float, output: str)
    """
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        return success, duration, output
    
    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start_time).total_seconds()
        return False, duration, "Test timed out after 300 seconds"
    
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        return False, duration, str(e)


def run_backend_tests(test_type="all"):
    """
    Run backend tests.
    
    Args:
        test_type: Type of tests to run (all, unit, integration, e2e)
    
    Returns:
        dict: Test results
    """
    backend_dir = Path(__file__).parent.parent
    results = {}
    
    test_files = {
        "unit_api": "tests/test_simple_server.py",
        "unit_llm": "tests/test_llm_providers.py",
        "e2e": "tests/test_e2e_complete.py",
    }
    
    if test_type == "all":
        files_to_run = test_files
    else:
        files_to_run = {k: v for k, v in test_files.items() if test_type in k}
    
    for test_name, test_file in files_to_run.items():
        print_section(f"Running Backend Tests: {test_name}")
        
        cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"]
        success, duration, output = run_command(cmd, test_name, cwd=backend_dir)
        
        results[f"backend_{test_name}"] = {
            "success": success,
            "duration": duration,
            "output": output
        }
        
        if success:
            print_success(f"{test_name} passed in {duration:.2f}s")
        else:
            print_failure(f"{test_name} failed in {duration:.2f}s")
            print(f"\n{output}\n")
    
    return results


def run_frontend_tests():
    """
    Run frontend tests.
    
    Returns:
        dict: Test results
    """
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    results = {}
    
    print_section("Running Frontend Tests")
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print_warning("node_modules not found. Run 'npm install' first.")
        return {"frontend_tests": {"success": False, "duration": 0, "output": "Dependencies not installed"}}
    
    cmd = ["npm", "run", "test"]
    success, duration, output = run_command(cmd, "frontend tests", cwd=frontend_dir)
    
    results["frontend_tests"] = {
        "success": success,
        "duration": duration,
        "output": output
    }
    
    if success:
        print_success(f"Frontend tests passed in {duration:.2f}s")
    else:
        print_failure(f"Frontend tests failed in {duration:.2f}s")
        print(f"\n{output}\n")
    
    return results


def check_server_health():
    """
    Check if backend server is running.
    
    Returns:
        bool: True if server is healthy
    """
    try:
        import requests
        response = requests.get("http://localhost:8001/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_ollama():
    """
    Check if Ollama is running.
    
    Returns:
        bool: True if Ollama is running
    """
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def run_live_integration_tests():
    """
    Run integration tests against live servers.
    
    Returns:
        dict: Test results
    """
    results = {}
    
    print_section("Running Live Integration Tests")
    
    # Check prerequisites
    server_running = check_server_health()
    ollama_running = check_ollama()
    
    if not server_running:
        print_warning("Backend server not running on port 8001")
        print_warning("Start with: cd backend && python simple_server.py")
        return {"integration_live": {"success": False, "duration": 0, "output": "Server not running"}}
    
    if not ollama_running:
        print_warning("Ollama not running on port 11434")
        print_warning("Start with: ollama serve")
        # Don't fail, just warn - tests can still run in demo mode
    
    print_success("Backend server is running")
    if ollama_running:
        print_success("Ollama is running")
    
    # Run live integration test
    backend_dir = Path(__file__).parent.parent
    cmd = [sys.executable, "-m", "pytest", "tests/test_e2e_complete.py::TestCompleteUserJourney", "-v"]
    success, duration, output = run_command(cmd, "live integration", cwd=backend_dir)
    
    results["integration_live"] = {
        "success": success,
        "duration": duration,
        "output": output
    }
    
    if success:
        print_success(f"Live integration tests passed in {duration:.2f}s")
    else:
        print_failure(f"Live integration tests failed in {duration:.2f}s")
        print(f"\n{output}\n")
    
    return results


def generate_report(all_results):
    """
    Generate final test report.
    
    Args:
        all_results: Dictionary of all test results
    """
    print_header("TEST SUMMARY")
    
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results.values() if r["success"])
    failed_tests = total_tests - passed_tests
    total_duration = sum(r["duration"] for r in all_results.values())
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {Colors.OKGREEN}{passed_tests}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed_tests}{Colors.ENDC}")
    print(f"Total Duration: {total_duration:.2f}s")
    print()
    
    # Detailed results
    print_section("Detailed Results")
    for test_name, result in all_results.items():
        status = f"{Colors.OKGREEN}PASSED{Colors.ENDC}" if result["success"] else f"{Colors.FAIL}FAILED{Colors.ENDC}"
        print(f"{test_name:30} {status}  ({result['duration']:.2f}s)")
    
    # Overall status
    print()
    if failed_tests == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.ENDC}")
        return 0
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.ENDC}")
        return 1


def main():
    """Main test runner."""
    print_header("COMPREHENSIVE TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = {}
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Run comprehensive tests")
    parser.add_argument("--backend-only", action="store_true", help="Run only backend tests")
    parser.add_argument("--frontend-only", action="store_true", help="Run only frontend tests")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--live", action="store_true", help="Run live integration tests")
    parser.add_argument("--quick", action="store_true", help="Run quick essential tests only")
    args = parser.parse_args()
    
    # Determine what to run
    if args.quick:
        print_warning("Running quick test suite (essential tests only)")
        all_results.update(run_backend_tests("unit"))
    elif args.backend_only:
        all_results.update(run_backend_tests())
    elif args.frontend_only:
        all_results.update(run_frontend_tests())
    elif args.integration_only:
        all_results.update(run_backend_tests("e2e"))
    elif args.live:
        all_results.update(run_live_integration_tests())
    else:
        # Run all tests
        all_results.update(run_backend_tests())
        all_results.update(run_frontend_tests())
        if check_server_health():
            all_results.update(run_live_integration_tests())
        else:
            print_warning("Skipping live integration tests (server not running)")
    
    # Generate report
    exit_code = generate_report(all_results)
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
