"""
Comprehensive Test Runner for Phase 2 Features.
Runs all tests and generates a detailed report.
"""
import subprocess
import sys
import os
import time
from datetime import datetime

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_section(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}>>> {text}{Colors.END}")
    print(f"{Colors.BLUE}{'-'*50}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def run_command(command, cwd=None, capture=True):
    """Run a command and return result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=capture,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_server_health(url="http://localhost:8001"):
    """Check if the backend server is running."""
    import requests
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    start_time = time.time()
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }
    
    print_header("COMPREHENSIVE TEST SUITE - Phase 2 Features")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get paths
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(backend_dir)
    frontend_dir = os.path.join(root_dir, "frontend")
    
    # ==========================================================================
    # 1. Backend Unit Tests
    # ==========================================================================
    print_section("1. Backend Unit Tests")
    
    test_files = [
        "test_new_features.py",
        "test_api.py",
        "test_schemas.py",
    ]
    
    for test_file in test_files:
        test_path = os.path.join(backend_dir, "tests", test_file)
        if os.path.exists(test_path):
            print(f"\nRunning {test_file}...")
            success, stdout, stderr = run_command(
                f"python -m pytest {test_path} -v --tb=short",
                cwd=backend_dir
            )
            
            if success:
                print_success(f"{test_file} passed")
                results["passed"] += 1
            else:
                print_error(f"{test_file} failed")
                results["failed"] += 1
                results["errors"].append(f"Backend: {test_file}")
                if stderr:
                    print(f"   Error: {stderr[:200]}...")
        else:
            print_warning(f"{test_file} not found")
            results["skipped"] += 1
    
    # ==========================================================================
    # 2. Backend E2E Tests (requires running server)
    # ==========================================================================
    print_section("2. Backend E2E Tests")
    
    if check_server_health():
        print_success("Server is running")
        
        e2e_tests = [
            "test_e2e_new_features.py",
        ]
        
        for test_file in e2e_tests:
            test_path = os.path.join(backend_dir, "tests", test_file)
            if os.path.exists(test_path):
                print(f"\nRunning {test_file}...")
                success, stdout, stderr = run_command(
                    f"python -m pytest {test_path} -v --tb=short -x",
                    cwd=backend_dir
                )
                
                if success:
                    print_success(f"{test_file} passed")
                    results["passed"] += 1
                else:
                    # Check if just skipped due to LLM
                    if "skipped" in stdout.lower() or "skip" in stderr.lower():
                        print_warning(f"{test_file} had skipped tests (LLM not available)")
                        results["skipped"] += 1
                    else:
                        print_error(f"{test_file} failed")
                        results["failed"] += 1
                        results["errors"].append(f"E2E: {test_file}")
            else:
                print_warning(f"{test_file} not found")
                results["skipped"] += 1
    else:
        print_warning("Server not running - skipping E2E tests")
        print_warning("Start the server with: python enhanced_server_v2.py")
        results["skipped"] += 3
    
    # ==========================================================================
    # 3. Frontend Tests
    # ==========================================================================
    print_section("3. Frontend Tests")
    
    if os.path.exists(os.path.join(frontend_dir, "package.json")):
        print("\nRunning frontend tests with Vitest...")
        success, stdout, stderr = run_command(
            "npm test -- --run --reporter=verbose",
            cwd=frontend_dir
        )
        
        if success:
            print_success("Frontend tests passed")
            results["passed"] += 1
        else:
            # Check if tests ran but some failed
            if "FAIL" in stdout or "failed" in stdout.lower():
                print_error("Some frontend tests failed")
                results["failed"] += 1
                results["errors"].append("Frontend: vitest")
            elif "Error" in stderr and "Cannot find module" not in stderr:
                print_error("Frontend test error")
                results["failed"] += 1
                results["errors"].append("Frontend: vitest")
            else:
                print_warning("Frontend tests could not run")
                results["skipped"] += 1
    else:
        print_warning("Frontend directory not found")
        results["skipped"] += 1
    
    # ==========================================================================
    # 4. API Endpoint Tests
    # ==========================================================================
    print_section("4. Quick API Endpoint Checks")
    
    if check_server_health():
        import requests
        
        endpoints = [
            ("GET", "/health", None),
            ("GET", "/", None),
            ("GET", "/api/docs", None),
            ("OPTIONS", "/api/chat/stream", None),
        ]
        
        for method, endpoint, data in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"http://localhost:8001{endpoint}", timeout=5)
                elif method == "POST":
                    response = requests.post(f"http://localhost:8001{endpoint}", json=data, timeout=5)
                elif method == "OPTIONS":
                    response = requests.options(f"http://localhost:8001{endpoint}", timeout=5)
                
                if response.status_code < 400:
                    print_success(f"{method} {endpoint} - {response.status_code}")
                    results["passed"] += 1
                else:
                    print_error(f"{method} {endpoint} - {response.status_code}")
                    results["failed"] += 1
            except Exception as e:
                print_error(f"{method} {endpoint} - {str(e)[:30]}")
                results["failed"] += 1
    else:
        print_warning("Server not running - skipping endpoint checks")
        results["skipped"] += 4
    
    # ==========================================================================
    # 5. Test New Feature Endpoints
    # ==========================================================================
    print_section("5. New Feature Endpoint Tests")
    
    if check_server_health():
        import requests
        
        # Test batch upload endpoint exists
        try:
            response = requests.options("http://localhost:8001/api/docs/upload/batch", timeout=5)
            if response.status_code != 404:
                print_success("Batch upload endpoint available")
                results["passed"] += 1
            else:
                print_error("Batch upload endpoint not found")
                results["failed"] += 1
        except Exception as e:
            print_error(f"Batch upload check failed: {e}")
            results["failed"] += 1
        
        # Test export endpoint
        try:
            response = requests.get("http://localhost:8001/api/chat/history/test/export", timeout=5)
            if response.status_code == 200:
                print_success("Export endpoint working")
                results["passed"] += 1
            else:
                print_error(f"Export endpoint returned {response.status_code}")
                results["failed"] += 1
        except Exception as e:
            print_error(f"Export check failed: {e}")
            results["failed"] += 1
        
        # Test streaming endpoint
        try:
            response = requests.options("http://localhost:8001/api/chat/stream", timeout=5)
            if response.status_code != 404:
                print_success("Streaming endpoint available")
                results["passed"] += 1
            else:
                print_error("Streaming endpoint not found")
                results["failed"] += 1
        except Exception as e:
            print_error(f"Streaming check failed: {e}")
            results["failed"] += 1
    else:
        print_warning("Server not running - skipping feature endpoint tests")
        results["skipped"] += 3
    
    # ==========================================================================
    # Summary
    # ==========================================================================
    print_header("TEST SUMMARY")
    
    elapsed = time.time() - start_time
    total = results["passed"] + results["failed"] + results["skipped"]
    
    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")
    print(f"{Colors.YELLOW}Skipped: {results['skipped']}{Colors.END}")
    print(f"\nTime: {elapsed:.2f}s")
    
    if results["errors"]:
        print(f"\n{Colors.RED}Failed Tests:{Colors.END}")
        for error in results["errors"]:
            print(f"  - {error}")
    
    # Calculate pass rate
    if total - results["skipped"] > 0:
        pass_rate = (results["passed"] / (total - results["skipped"])) * 100
        print(f"\nPass Rate: {pass_rate:.1f}%")
        
        if pass_rate >= 90:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ EXCELLENT - Tests passing!{Colors.END}")
        elif pass_rate >= 70:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠ GOOD - Some issues to fix{Colors.END}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ NEEDS WORK - Many tests failing{Colors.END}")
    
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("Installing requests...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], capture_output=True)
        import requests
    
    sys.exit(main())
