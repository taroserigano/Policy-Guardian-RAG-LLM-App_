"""
Quick Comparison Test - Shows side-by-side responses
"""
import requests

def ask_model(model, question):
    """Ask a model a question and return the answer"""
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": question}],
                "stream": False
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["message"]["content"]
        return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

# Test question
question = "How many vacation days do employees get per year?"

print("="*80)
print(f"QUESTION: {question}")
print("="*80)

print("\n📦 BASE MODEL (llama3.1:8b):")
print("-"*80)
base_answer = ask_model("llama3.1:8b", question)
print(base_answer)

print("\n✨ FINE-TUNED MODEL (policy-compliance-llm):")
print("-"*80)
ft_answer = ask_model("policy-compliance-llm", question)
print(ft_answer)

print("\n" + "="*80)
print("COMPARISON:")
print("="*80)

# Check for key information
if "20" in ft_answer and ("20" not in base_answer or "annual" not in base_answer.lower()):
    print("✅ Fine-tuned model correctly mentioned 20 days!")
elif "20" in base_answer and "20" in ft_answer:
    print("⚖️  Both models mentioned 20 days")
else:
    print("📊 Compare the responses above")

print("\nExpected: 20 days of paid annual leave per year")
