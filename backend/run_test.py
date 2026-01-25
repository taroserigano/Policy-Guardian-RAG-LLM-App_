"""
Run comparison and save results to file
"""
import requests
import json
import time

def ask_model(model, question):
    try:
        print(f"Querying {model}...")
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": question}],
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["message"]["content"]
        return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

# Run tests
results = []

test_questions = [
    {
        "q": "How many vacation days do employees get per year?",
        "keywords": ["20", "annual", "days"]
    },
    {
        "q": "How many sick leave days are available?",
        "keywords": ["10", "sick"]
    },
    {
        "q": "What is the maternity leave policy?",
        "keywords": ["16", "week", "maternity"]
    }
]

print("Starting comparison tests...")
print("="*80)

for i, test in enumerate(test_questions, 1):
    question = test["q"]
    keywords = test["keywords"]
    
    print(f"\nTest {i}/{len(test_questions)}: {question}")
    print("-"*80)
    
    # Ask base model
    base_answer = ask_model("llama3.1:8b", question)
    base_score = sum(1 for kw in keywords if kw in base_answer.lower())
    
    # Ask fine-tuned model
    ft_answer = ask_model("policy-compliance-llm", question)
    ft_score = sum(1 for kw in keywords if kw in ft_answer.lower())
    
    result = {
        "question": question,
        "keywords": keywords,
        "base_answer": base_answer[:300],
        "base_score": base_score,
        "ft_answer": ft_answer[:300],
        "ft_score": ft_score,
        "improvement": ft_score - base_score
    }
    results.append(result)
    
    print(f"\nBase Model Score: {base_score}/{len(keywords)}")
    print(f"Base Answer: {base_answer[:200]}...")
    print(f"\nFine-Tuned Score: {ft_score}/{len(keywords)}")
    print(f"Fine-Tuned Answer: {ft_answer[:200]}...")
    print(f"\nImprovement: {'+' if result['improvement'] > 0 else ''}{result['improvement']}")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

total_keywords = sum(len(r["keywords"]) for r in results)
base_total = sum(r["base_score"] for r in results)
ft_total = sum(r["ft_score"] for r in results)

print(f"\nBase Model Accuracy: {base_total}/{total_keywords} ({100*base_total/total_keywords:.1f}%)")
print(f"Fine-Tuned Accuracy: {ft_total}/{total_keywords} ({100*ft_total/total_keywords:.1f}%)")
print(f"Improvement: +{ft_total - base_total} keywords ({100*(ft_total-base_total)/total_keywords:.1f}%)")

wins = sum(1 for r in results if r["improvement"] > 0)
print(f"\nQuestions where fine-tuned won: {wins}/{len(results)}")

# Save to file
with open("comparison_results.json", "w") as f:
    json.dump({
        "summary": {
            "base_accuracy": f"{base_total}/{total_keywords}",
            "ft_accuracy": f"{ft_total}/{total_keywords}",
            "improvement": ft_total - base_total,
            "wins": wins
        },
        "details": results
    }, f, indent=2)

print("\n✅ Results saved to: comparison_results.json")
