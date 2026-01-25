#!/usr/bin/env python3
"""
Automated Model Comparison Test - No Unicode
"""
import requests
import json
import sys
from datetime import datetime

print("=" * 80)
print("FINE-TUNED MODEL COMPARISON TEST")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Check Ollama connection
print("Checking Ollama connection...")
try:
    response = requests.get("http://localhost:11434/api/version", timeout=5)
    if response.status_code == 200:
        print(f"[OK] Ollama is running (version: {response.json().get('version', 'unknown')})")
    else:
        print(f"[ERROR] Ollama returned status {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"[ERROR] Cannot connect to Ollama: {e}")
    print("Make sure Ollama is running!")
    sys.exit(1)

# Check models
print("\nChecking available models...")
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    models = [m['name'] for m in response.json().get("models", [])]
    
    has_base = any("llama3.1" in m for m in models)
    has_ft = any("policy-compliance-llm" in m for m in models)
    
    print(f"  llama3.1:8b: {'[OK]' if has_base else '[NOT FOUND]'}")
    print(f"  policy-compliance-llm: {'[OK]' if has_ft else '[NOT FOUND]'}")
    
    if not has_base or not has_ft:
        print("\n[ERROR] Required models not found!")
        print("Available models:", models)
        sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error checking models: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("RUNNING TESTS (3 questions)")
print("=" * 80)

def test_model(model_name, question):
    """Test a model with a question"""
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": question}],
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["message"]["content"]
        return None
    except Exception as e:
        return None

# Test cases
tests = [
    {
        "question": "How many vacation days do employees get per year?",
        "keywords": ["20", "annual", "days", "year"],
        "expected": "20 days of paid annual leave"
    },
    {
        "question": "How many sick leave days are available?",
        "keywords": ["10", "sick", "days"],
        "expected": "10 days of sick leave"
    },
    {
        "question": "What is the maternity leave policy?",
        "keywords": ["16", "week", "maternity"],
        "expected": "16 weeks (8 paid, 8 unpaid)"
    }
]

results = []

for i, test in enumerate(tests, 1):
    print(f"\n{'-' * 80}")
    print(f"TEST {i}/{len(tests)}: {test['question']}")
    print(f"Expected: {test['expected']}")
    print(f"{'-' * 80}")
    
    # Test base model
    print(f"\n[BASE] Testing llama3.1:8b...")
    base_answer = test_model("llama3.1:8b", test['question'])
    
    if base_answer:
        base_score = sum(1 for kw in test['keywords'] if kw.lower() in base_answer.lower())
        print(f"  Score: {base_score}/{len(test['keywords'])} keywords")
        print(f"  Answer: {base_answer[:200]}...")
    else:
        base_score = 0
        base_answer = "[ERROR: No response]"
        print(f"  [FAILED] No response")
    
    # Test fine-tuned model
    print(f"\n[FINETUNED] Testing policy-compliance-llm...")
    ft_answer = test_model("policy-compliance-llm", test['question'])
    
    if ft_answer:
        ft_score = sum(1 for kw in test['keywords'] if kw.lower() in ft_answer.lower())
        print(f"  Score: {ft_score}/{len(test['keywords'])} keywords")
        print(f"  Answer: {ft_answer[:200]}...")
    else:
        ft_score = 0
        ft_answer = "[ERROR: No response]"
        print(f"  [FAILED] No response")
    
    # Comparison
    improvement = ft_score - base_score
    if improvement > 0:
        print(f"\n  [RESULT] Fine-tuned is MORE accurate (+{improvement} keywords)")
    elif improvement == 0:
        print(f"\n  [RESULT] Both models equally accurate")
    else:
        print(f"\n  [RESULT] Base model was more accurate")
    
    results.append({
        "question": test['question'],
        "keywords": test['keywords'],
        "expected": test['expected'],
        "base_score": base_score,
        "base_answer": base_answer,
        "ft_score": ft_score,
        "ft_answer": ft_answer,
        "improvement": improvement
    })

# Summary
print("\n" + "=" * 80)
print("FINAL RESULTS")
print("=" * 80)

total_keywords = sum(len(t['keywords']) for t in tests)
base_total = sum(r['base_score'] for r in results)
ft_total = sum(r['ft_score'] for r in results)

base_pct = 100 * base_total / total_keywords
ft_pct = 100 * ft_total / total_keywords
improvement_pct = ft_pct - base_pct

print(f"\nACCURACY (Keyword Detection):")
print(f"   Base Model:       {base_total}/{total_keywords} ({base_pct:.1f}%)")
print(f"   Fine-Tuned Model: {ft_total}/{total_keywords} ({ft_pct:.1f}%)")

if improvement_pct > 0:
    print(f"   Improvement:      +{ft_total - base_total} keywords (+{improvement_pct:.1f}%)")
else:
    print(f"   Change:           {ft_total - base_total} keywords ({improvement_pct:+.1f}%)")

wins = sum(1 for r in results if r['improvement'] > 0)
ties = sum(1 for r in results if r['improvement'] == 0)
losses = sum(1 for r in results if r['improvement'] < 0)

print(f"\nQUESTIONS:")
print(f"   Wins:   {wins}/{len(tests)} (fine-tuned better)")
print(f"   Ties:   {ties}/{len(tests)} (equal)")
print(f"   Losses: {losses}/{len(tests)} (base better)")

# Overall assessment
print(f"\nASSESSMENT:")
if improvement_pct > 20:
    print(f"   [EXCELLENT] Fine-tuning was very effective (+{improvement_pct:.0f}%)")
elif improvement_pct > 10:
    print(f"   [GOOD] Fine-tuning helped significantly (+{improvement_pct:.0f}%)")
elif improvement_pct > 0:
    print(f"   [MINOR] Some improvement (+{improvement_pct:.0f}%)")
else:
    print(f"   [WARNING] No improvement - Consider more training")

# Save results
output = {
    "timestamp": datetime.now().isoformat(),
    "summary": {
        "base_accuracy": f"{base_total}/{total_keywords}",
        "base_percentage": round(base_pct, 1),
        "ft_accuracy": f"{ft_total}/{total_keywords}",
        "ft_percentage": round(ft_pct, 1),
        "improvement": round(improvement_pct, 1),
        "wins": wins,
        "ties": ties,
        "losses": losses
    },
    "tests": results
}

with open("comparison_results.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\nDetailed results saved to: comparison_results.json")
print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
