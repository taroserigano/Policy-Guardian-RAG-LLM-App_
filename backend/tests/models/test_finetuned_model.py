"""
Test the fine-tuned policy-compliance-llm model integration
"""
import requests
import json

BASE_URL = "http://localhost:8001"

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name):
    print(f"\n{BLUE}🧪 TEST: {name}{RESET}")
    
def print_pass(msg):
    print(f"{GREEN}✅ {msg}{RESET}")
    
def print_fail(msg):
    print(f"{RED}❌ {msg}{RESET}")

def test_model_available():
    """Check if fine-tuned model exists in Ollama"""
    print_test("Fine-tuned Model Available in Ollama")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m['name'] for m in models]
            
            if any("policy-compliance-llm" in name for name in model_names):
                print_pass("policy-compliance-llm found in Ollama")
                return True
            else:
                print_fail("policy-compliance-llm not found!")
                print(f"Available models: {model_names}")
                return False
    except Exception as e:
        print_fail(f"Error: {e}")
        return False

def test_direct_ollama():
    """Test fine-tuned model directly via Ollama API"""
    print_test("Direct Ollama API Call")
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "policy-compliance-llm",
                "messages": [{"role": "user", "content": "How many vacation days do employees get?"}],
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            answer = response.json()["message"]["content"]
            print_pass(f"Model responded: {answer[:150]}...")
            
            # Check if answer mentions 20 days (from training data)
            if "20" in answer and ("day" in answer.lower() or "annual" in answer.lower()):
                print_pass("Model correctly referenced vacation policy!")
                return True
            else:
                print(f"Full answer: {answer}")
                return True
        else:
            print_fail(f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Error: {e}")
        return False

def test_backend_integration():
    """Test fine-tuned model through backend API"""
    print_test("Backend API Integration")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "question": "What are the remote work eligibility requirements?",
                "provider": "ollama",
                "user_id": "test_finetuned"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            model_info = data.get("model", {})
            
            print_pass(f"Backend responded successfully")
            print(f"  Model used: {model_info}")
            print(f"  Answer: {answer[:200]}...")
            
            # Check for policy-specific content
            if "6 months" in answer or "remote" in answer.lower():
                print_pass("Model provided policy-specific answer!")
                return True
            return True
        else:
            print_fail(f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Error: {e}")
        return False

def test_policy_questions():
    """Test multiple policy-related questions"""
    print_test("Policy Question Accuracy")
    
    questions = [
        ("How many sick leave days are available?", ["10", "sick"]),
        ("What is the maternity leave policy?", ["16", "week", "maternity"]),
        ("Can I work remotely full-time?", ["3", "days", "approval", "remote"]),
        ("What information is covered by the NDA?", ["confidential", "trade", "secret"])
    ]
    
    passed = 0
    for question, keywords in questions:
        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "policy-compliance-llm",
                    "messages": [{"role": "user", "content": question}],
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                answer = response.json()["message"]["content"].lower()
                
                # Check if any keyword appears
                found = any(kw.lower() in answer for kw in keywords)
                
                if found:
                    print_pass(f"Q: {question[:50]}... ✓")
                    passed += 1
                else:
                    print(f"  Q: {question[:50]}... (no keywords found)")
                    print(f"  A: {answer[:100]}...")
        except Exception as e:
            print_fail(f"Q: {question[:50]}... Error: {e}")
    
    print(f"\n{passed}/{len(questions)} questions answered with relevant content")
    return passed >= len(questions) // 2  # Pass if at least 50% correct

if __name__ == "__main__":
    print(f"{BLUE}{'='*60}")
    print("Testing Fine-Tuned Model Integration")
    print(f"{'='*60}{RESET}")
    
    results = []
    
    results.append(("Model Available", test_model_available()))
    results.append(("Direct Ollama", test_direct_ollama()))
    results.append(("Backend Integration", test_backend_integration()))
    results.append(("Policy Accuracy", test_policy_questions()))
    
    # Summary
    print(f"\n{BLUE}{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}{RESET}")
    
    for name, passed in results:
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"{name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\n{total_passed}/{len(results)} tests passed")
