"""
Evaluate Fine-Tuned Policy Compliance Model

This script tests the fine-tuned model against a set of policy compliance questions
and compares its performance to the base model.

Usage:
    python evaluate_model.py --model policy-compliance-llm
    python evaluate_model.py --model policy-compliance-llm --base_model llama3.1:8b
"""

import os
import json
import argparse
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict, Any
import time

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


# Test questions covering different policy areas
TEST_QUESTIONS = [
    # Data Privacy
    {
        "question": "What are the key requirements for handling personal data according to the data privacy policy?",
        "category": "data_privacy",
        "expected_topics": ["consent", "data minimization", "security", "retention"]
    },
    {
        "question": "How long should employee personal data be retained after they leave the company?",
        "category": "data_privacy",
        "expected_topics": ["retention period", "deletion", "legal requirements"]
    },
    
    # Information Security
    {
        "question": "What are the password requirements for system access?",
        "category": "information_security",
        "expected_topics": ["complexity", "length", "change frequency", "MFA"]
    },
    {
        "question": "What should an employee do if they suspect a security breach?",
        "category": "information_security",
        "expected_topics": ["report", "IT security", "incident response", "immediate action"]
    },
    
    # Remote Work
    {
        "question": "What equipment is provided for remote work and who is responsible for it?",
        "category": "remote_work",
        "expected_topics": ["laptop", "company property", "maintenance", "return"]
    },
    {
        "question": "What are the security requirements for working from home?",
        "category": "remote_work",
        "expected_topics": ["VPN", "secure network", "encryption", "physical security"]
    },
    
    # Employee Leave
    {
        "question": "How many days of annual leave are employees entitled to?",
        "category": "employee_leave",
        "expected_topics": ["days", "accrual", "carry over"]
    },
    {
        "question": "What is the process for requesting sick leave?",
        "category": "employee_leave",
        "expected_topics": ["notification", "documentation", "manager approval"]
    },
    
    # NDA
    {
        "question": "What information is covered under the non-disclosure agreement?",
        "category": "nda",
        "expected_topics": ["confidential", "trade secrets", "proprietary", "business information"]
    },
    {
        "question": "How long does the confidentiality obligation last after employment ends?",
        "category": "nda",
        "expected_topics": ["duration", "years", "perpetual", "termination"]
    },
    
    # Compliance Scenarios
    {
        "question": "An employee wants to use personal cloud storage to save work files. Is this allowed?",
        "category": "scenario",
        "expected_topics": ["not allowed", "approved services", "data security", "policy violation"]
    },
    {
        "question": "A contractor asks for access to the customer database for a project. What should the manager do?",
        "category": "scenario",
        "expected_topics": ["NDA", "access control", "need to know", "approval process"]
    },
]


async def query_model(model: str, question: str) -> Dict[str, Any]:
    """Query Ollama model and measure response time."""
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a compliance assistant. Answer questions about corporate policies accurately and concisely."
                    },
                    {"role": "user", "content": question}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower for more consistent evaluation
                    "num_predict": 512
                }
            }
        )
        response.raise_for_status()
        result = response.json()
    
    elapsed_time = time.time() - start_time
    
    return {
        "answer": result["message"]["content"],
        "time": elapsed_time
    }


def score_response(response: str, expected_topics: List[str]) -> float:
    """Score response based on coverage of expected topics."""
    response_lower = response.lower()
    topics_found = sum(1 for topic in expected_topics if topic.lower() in response_lower)
    return topics_found / len(expected_topics) if expected_topics else 0


async def evaluate_model(model: str, questions: List[Dict] = None) -> Dict[str, Any]:
    """Evaluate a model on test questions."""
    if questions is None:
        questions = TEST_QUESTIONS
    
    results = []
    total_time = 0
    total_score = 0
    
    print(f"\nEvaluating model: {model}")
    print("=" * 60)
    
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] {q['category'].upper()}")
        print(f"Q: {q['question'][:80]}...")
        
        try:
            result = await query_model(model, q["question"])
            score = score_response(result["answer"], q["expected_topics"])
            
            results.append({
                "question": q["question"],
                "category": q["category"],
                "answer": result["answer"],
                "time": result["time"],
                "score": score,
                "expected_topics": q["expected_topics"]
            })
            
            total_time += result["time"]
            total_score += score
            
            print(f"A: {result['answer'][:100]}...")
            print(f"   Score: {score:.1%} | Time: {result['time']:.1f}s")
            
        except Exception as e:
            print(f"   Error: {e}")
            results.append({
                "question": q["question"],
                "category": q["category"],
                "error": str(e),
                "score": 0,
                "time": 0
            })
    
    avg_score = total_score / len(questions) if questions else 0
    avg_time = total_time / len(questions) if questions else 0
    
    return {
        "model": model,
        "total_questions": len(questions),
        "average_score": avg_score,
        "average_time": avg_time,
        "results": results
    }


async def compare_models(fine_tuned: str, base_model: str):
    """Compare fine-tuned model against base model."""
    print("\n" + "=" * 60)
    print("MODEL COMPARISON EVALUATION")
    print("=" * 60)
    
    # Evaluate both models
    ft_results = await evaluate_model(fine_tuned)
    base_results = await evaluate_model(base_model)
    
    # Print comparison
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    
    print(f"\n{'Metric':<25} {'Fine-tuned':>15} {'Base':>15} {'Diff':>15}")
    print("-" * 70)
    
    score_diff = ft_results["average_score"] - base_results["average_score"]
    time_diff = ft_results["average_time"] - base_results["average_time"]
    
    print(f"{'Average Score':<25} {ft_results['average_score']:>14.1%} {base_results['average_score']:>14.1%} {score_diff:>+14.1%}")
    print(f"{'Average Time (s)':<25} {ft_results['average_time']:>15.1f} {base_results['average_time']:>15.1f} {time_diff:>+15.1f}")
    
    # Category breakdown
    print("\n\nBy Category:")
    print("-" * 70)
    
    categories = set(r["category"] for r in ft_results["results"])
    
    for cat in sorted(categories):
        ft_cat = [r for r in ft_results["results"] if r["category"] == cat]
        base_cat = [r for r in base_results["results"] if r["category"] == cat]
        
        ft_avg = sum(r.get("score", 0) for r in ft_cat) / len(ft_cat) if ft_cat else 0
        base_avg = sum(r.get("score", 0) for r in base_cat) / len(base_cat) if base_cat else 0
        diff = ft_avg - base_avg
        
        print(f"  {cat:<23} {ft_avg:>14.1%} {base_avg:>14.1%} {diff:>+14.1%}")
    
    # Save results
    output = {
        "fine_tuned": ft_results,
        "base_model": base_results,
        "comparison": {
            "score_improvement": score_diff,
            "time_difference": time_diff
        }
    }
    
    output_path = Path(__file__).parent.parent / "outputs" / "evaluation_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n\nDetailed results saved to: {output_path}")
    
    return output


async def main():
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned policy compliance model")
    parser.add_argument("--model", type=str, default="policy-compliance-llm",
                        help="Fine-tuned model name in Ollama")
    parser.add_argument("--base_model", type=str, default="llama3.1:8b",
                        help="Base model to compare against")
    parser.add_argument("--compare", action="store_true",
                        help="Compare fine-tuned model against base model")
    parser.add_argument("--questions", type=str, default=None,
                        help="Path to custom questions JSON file")
    
    args = parser.parse_args()
    
    # Check Ollama availability
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            models = [m["name"] for m in response.json().get("models", [])]
            print(f"Available models: {', '.join(models)}")
    except Exception as e:
        print(f"Error: Cannot connect to Ollama: {e}")
        return
    
    # Load custom questions if provided
    questions = TEST_QUESTIONS
    if args.questions:
        with open(args.questions, "r") as f:
            questions = json.load(f)
    
    # Run evaluation
    if args.compare:
        await compare_models(args.model, args.base_model)
    else:
        results = await evaluate_model(args.model, questions)
        
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        print(f"Model: {results['model']}")
        print(f"Questions: {results['total_questions']}")
        print(f"Average Score: {results['average_score']:.1%}")
        print(f"Average Time: {results['average_time']:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
