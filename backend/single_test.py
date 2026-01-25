"""
Single Question Comparison - Quick Test
"""
import requests
import time

def ask_ollama(model, question):
    """Ask a model a question"""
    print(f"\nAsking {model}...")
    start = time.time()
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": question}],
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=90
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            answer = response.json()["message"]["content"]
            return answer, elapsed
        return f"ERROR: {response.status_code}", elapsed
    except Exception as e:
        return f"ERROR: {e}", 0

# Question
question = "How many vacation days do employees get per year?"
keywords = ["20", "annual", "days"]

print("=" * 80)
print("QUICK COMPARISON TEST")
print("=" * 80)
print(f"\nQuestion: {question}")
print(f"Looking for: 20 days of paid annual leave")
print("\n" + "=" * 80)

# Test base model
base_answer, base_time = ask_ollama("llama3.1:8b", question)
base_score = sum(1 for kw in keywords if kw in base_answer.lower())

print(f"\n[BASE MODEL: llama3.1:8b]")
print(f"Time: {base_time:.1f}s")
print(f"Score: {base_score}/{len(keywords)} keywords found")
print(f"\nAnswer:")
print(base_answer)

# Test fine-tuned model  
ft_answer, ft_time = ask_ollama("policy-compliance-llm", question)
ft_score = sum(1 for kw in keywords if kw in ft_answer.lower())

print(f"\n" + "=" * 80)
print(f"[FINE-TUNED MODEL: policy-compliance-llm]")
print(f"Time: {ft_time:.1f}s")
print(f"Score: {ft_score}/{len(keywords)} keywords found")
print(f"\nAnswer:")
print(ft_answer)

# Comparison
print("\n" + "=" * 80)
print("COMPARISON")
print("=" * 80)
print(f"\nBase Model:       {base_score}/{len(keywords)} keywords ({100*base_score/len(keywords):.0f}%)")
print(f"Fine-Tuned Model: {ft_score}/{len(keywords)} keywords ({100*ft_score/len(keywords):.0f}%)")

improvement = ft_score - base_score
if improvement > 0:
    print(f"\n[RESULT] Fine-tuned model is {improvement} keywords more accurate!")
    print("[SUCCESS] Fine-tuning improved the model!")
elif improvement == 0:
    print(f"\n[RESULT] Both models performed equally")
else:
    print(f"\n[RESULT] Base model was more accurate")

print("\nExpected: Fine-tuned should mention '20', 'annual', and 'days'")
print("=" * 80)
