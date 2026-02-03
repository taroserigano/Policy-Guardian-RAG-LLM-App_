"""
Compare Fine-Tuned vs Base Model Performance
Tests policy-compliance-llm against llama3.1:8b to measure improvements
"""
import requests
import json
import time
from typing import Dict, List, Tuple

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

# Models to compare
FINETUNED_MODEL = "policy-compliance-llm"
BASE_MODEL = "llama3.1:8b"

# Test questions with expected key information
TEST_CASES = [
    {
        "question": "How many vacation days do employees get per year?",
        "keywords": ["20", "annual", "days", "year"],
        "context": "Should mention 20 days of paid annual leave"
    },
    {
        "question": "How many sick leave days are available?",
        "keywords": ["10", "sick", "days"],
        "context": "Should mention 10 days of sick leave"
    },
    {
        "question": "What is the maternity leave policy?",
        "keywords": ["16", "week", "maternity", "8"],
        "context": "Should mention 16 weeks (8 weeks paid, 8 unpaid)"
    },
    {
        "question": "How many days of remote work are allowed per week?",
        "keywords": ["2", "hybrid", "week", "remote"],
        "context": "Should mention up to 2 days/week for hybrid"
    },
    {
        "question": "What are the requirements for full remote work?",
        "keywords": ["3", "days", "approval", "department", "head"],
        "context": "Should mention 3+ days requires department head approval"
    },
    {
        "question": "What is the home office equipment stipend?",
        "keywords": ["500", "equipment", "75", "internet"],
        "context": "Should mention $500 home office stipend and $75/month internet"
    },
    {
        "question": "How long are employee records retained?",
        "keywords": ["7", "years", "retention"],
        "context": "Should mention 7 years retention period"
    },
    {
        "question": "What encryption is required for data?",
        "keywords": ["AES-256", "TLS", "encryption"],
        "context": "Should mention TLS 1.2+ and AES-256 encryption"
    },
    {
        "question": "How long is the NDA confidentiality obligation?",
        "keywords": ["5", "year", "confidentiality"],
        "context": "Should mention 5 year confidentiality obligation"
    },
    {
        "question": "What is considered confidential information in the NDA?",
        "keywords": ["trade", "secret", "technical", "business"],
        "context": "Should mention trade secrets, technical designs, business plans"
    }
]

def call_ollama(model: str, question: str) -> Tuple[str, float]:
    """
    Call Ollama API and return response with timing.
    Returns (answer, duration_seconds)
    """
    try:
        start = time.time()
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": question}],
                "stream": False,
                "options": {"temperature": 0.3}  # Lower temp for consistency
            },
            timeout=60
        )
        duration = time.time() - start
        
        if response.status_code == 200:
            answer = response.json()["message"]["content"]
            return answer, duration
        else:
            return f"[ERROR: {response.status_code}]", duration
    except Exception as e:
        return f"[ERROR: {e}]", 0

def score_answer(answer: str, keywords: List[str]) -> Tuple[int, List[str]]:
    """
    Score answer based on keyword presence.
    Returns (score, found_keywords)
    """
    answer_lower = answer.lower()
    found = [kw for kw in keywords if kw.lower() in answer_lower]
    score = len(found)
    return score, found

def print_header(text: str):
    """Print a section header"""
    print(f"\n{BOLD}{BLUE}{'='*80}")
    print(f"{text}")
    print(f"{'='*80}{RESET}\n")

def print_comparison(test_num: int, question: str, base_answer: str, base_time: float,
                    ft_answer: str, ft_time: float, keywords: List[str], context: str):
    """Print side-by-side comparison"""
    print(f"{BOLD}{CYAN}Test #{test_num}: {question}{RESET}")
    print(f"{YELLOW}Expected: {context}{RESET}\n")
    
    # Score both answers
    base_score, base_found = score_answer(base_answer, keywords)
    ft_score, ft_found = score_answer(ft_answer, keywords)
    
    # Base model
    print(f"{BOLD}Base Model (llama3.1:8b):{RESET}")
    print(f"  Time: {base_time:.2f}s")
    print(f"  Score: {base_score}/{len(keywords)} keywords found")
    if base_found:
        print(f"  Found: {', '.join(base_found)}")
    print(f"  Answer: {base_answer[:200]}...")
    
    print()
    
    # Fine-tuned model
    print(f"{BOLD}Fine-Tuned Model (policy-compliance-llm):{RESET}")
    print(f"  Time: {ft_time:.2f}s")
    print(f"  Score: {ft_score}/{len(keywords)} keywords found")
    if ft_found:
        print(f"  Found: {', '.join(ft_found)}")
    print(f"  Answer: {ft_answer[:200]}...")
    
    print()
    
    # Comparison
    if ft_score > base_score:
        print(f"{GREEN}✅ Fine-tuned model is MORE accurate (+{ft_score - base_score} keywords){RESET}")
    elif ft_score == base_score:
        print(f"{YELLOW}⚖️  Both models equally accurate{RESET}")
    else:
        print(f"{RED}❌ Base model was more accurate{RESET}")
    
    print(f"{'-'*80}\n")
    
    return base_score, ft_score

def print_summary(results: List[Dict]):
    """Print final summary statistics"""
    print_header("COMPARISON SUMMARY")
    
    base_total = sum(r['base_score'] for r in results)
    ft_total = sum(r['ft_score'] for r in results)
    base_time_total = sum(r['base_time'] for r in results)
    ft_time_total = sum(r['ft_time'] for r in results)
    
    total_keywords = sum(len(r['keywords']) for r in results)
    
    print(f"{BOLD}Accuracy (Keyword Detection):{RESET}")
    print(f"  Base Model:       {base_total}/{total_keywords} ({100*base_total/total_keywords:.1f}%)")
    print(f"  Fine-Tuned Model: {ft_total}/{total_keywords} ({100*ft_total/total_keywords:.1f}%)")
    
    improvement = ft_total - base_total
    if improvement > 0:
        print(f"  {GREEN}Improvement: +{improvement} keywords ({100*improvement/total_keywords:.1f}% boost){RESET}")
    elif improvement == 0:
        print(f"  {YELLOW}No change in keyword detection{RESET}")
    else:
        print(f"  {RED}Regression: {improvement} keywords{RESET}")
    
    print(f"\n{BOLD}Response Time:{RESET}")
    print(f"  Base Model:       {base_time_total:.2f}s (avg {base_time_total/len(results):.2f}s)")
    print(f"  Fine-Tuned Model: {ft_time_total:.2f}s (avg {ft_time_total/len(results):.2f}s)")
    
    time_diff = ft_time_total - base_time_total
    if abs(time_diff) < 2:
        print(f"  {YELLOW}Similar speed{RESET}")
    elif time_diff > 0:
        print(f"  {YELLOW}Fine-tuned is {time_diff:.1f}s slower{RESET}")
    else:
        print(f"  {GREEN}Fine-tuned is {-time_diff:.1f}s faster{RESET}")
    
    print(f"\n{BOLD}Questions Where Fine-Tuned Model Won:{RESET}")
    wins = [r for r in results if r['ft_score'] > r['base_score']]
    ties = [r for r in results if r['ft_score'] == r['base_score']]
    losses = [r for r in results if r['ft_score'] < r['base_score']]
    
    print(f"  Wins:   {GREEN}{len(wins)}{RESET} questions")
    print(f"  Ties:   {YELLOW}{len(ties)}{RESET} questions")
    print(f"  Losses: {RED}{len(losses)}{RESET} questions")
    
    if wins:
        print(f"\n{BOLD}Questions with Biggest Improvements:{RESET}")
        wins_sorted = sorted(wins, key=lambda r: r['ft_score'] - r['base_score'], reverse=True)
        for r in wins_sorted[:3]:
            diff = r['ft_score'] - r['base_score']
            print(f"  • {r['question'][:60]}... (+{diff} keywords)")
    
    print(f"\n{BOLD}Overall Assessment:{RESET}")
    accuracy_improvement = 100 * improvement / total_keywords
    
    if accuracy_improvement > 10:
        print(f"{GREEN}🎉 SIGNIFICANT IMPROVEMENT! Fine-tuning was very effective.{RESET}")
    elif accuracy_improvement > 5:
        print(f"{GREEN}✅ GOOD IMPROVEMENT! Fine-tuning helped noticeably.{RESET}")
    elif accuracy_improvement > 0:
        print(f"{YELLOW}✓ MINOR IMPROVEMENT. Fine-tuning helped slightly.{RESET}")
    else:
        print(f"{RED}⚠ NO IMPROVEMENT. Consider more training data or epochs.{RESET}")

def check_models():
    """Check if both models are available"""
    print(f"{BLUE}Checking model availability...{RESET}")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = [m['name'] for m in response.json().get("models", [])]
            
            base_available = any("llama3.1" in m for m in models)
            ft_available = any("policy-compliance-llm" in m for m in models)
            
            print(f"  Base Model (llama3.1:8b): {'✅' if base_available else '❌'}")
            print(f"  Fine-Tuned Model (policy-compliance-llm): {'✅' if ft_available else '❌'}")
            
            if not base_available:
                print(f"\n{RED}Base model not found. Run: ollama pull llama3.1:8b{RESET}")
                return False
            
            if not ft_available:
                print(f"\n{RED}Fine-tuned model not found. Make sure you imported it to Ollama.{RESET}")
                return False
            
            return True
        else:
            print(f"{RED}Cannot connect to Ollama{RESET}")
            return False
    except Exception as e:
        print(f"{RED}Error checking models: {e}{RESET}")
        return False

def main():
    print_header("Fine-Tuned vs Base Model Comparison Test")
    
    # Check models
    if not check_models():
        print(f"\n{RED}Cannot proceed without both models. Exiting.{RESET}")
        return
    
    print(f"\n{BOLD}Running {len(TEST_CASES)} test cases...{RESET}")
    print(f"This will take ~{len(TEST_CASES) * 1}min (approximate)\n")
    
    input(f"{YELLOW}Press Enter to start the comparison...{RESET}")
    
    results = []
    
    for i, test in enumerate(TEST_CASES, 1):
        question = test['question']
        keywords = test['keywords']
        context = test['context']
        
        print(f"\n{MAGENTA}[{i}/{len(TEST_CASES)}] Testing: {question}{RESET}")
        
        # Test base model
        print(f"  Querying base model...")
        base_answer, base_time = call_ollama(BASE_MODEL, question)
        
        # Test fine-tuned model
        print(f"  Querying fine-tuned model...")
        ft_answer, ft_time = call_ollama(FINETUNED_MODEL, question)
        
        # Compare
        base_score, ft_score = print_comparison(
            i, question, base_answer, base_time,
            ft_answer, ft_time, keywords, context
        )
        
        results.append({
            'question': question,
            'keywords': keywords,
            'base_score': base_score,
            'ft_score': ft_score,
            'base_time': base_time,
            'ft_time': ft_time,
            'base_answer': base_answer,
            'ft_answer': ft_answer
        })
    
    # Print summary
    print_summary(results)
    
    # Save detailed results
    output_file = "model_comparison_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{GREEN}Detailed results saved to: {output_file}{RESET}")

if __name__ == "__main__":
    main()
