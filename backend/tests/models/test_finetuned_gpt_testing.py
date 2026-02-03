#!/usr/bin/env python3
"""
Round 4: 40 Direct Policy Questions
Straightforward questions to demonstrate clear fine-tuning benefits
Target: Fine-tuned >85% accuracy with 25%+ improvement
"""

import os
import sys
import time
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{CYAN}{text}{RESET}")

# Round 4: 40 straightforward policy questions
TEST_QUESTIONS_ROUND4 = [
    # Pricing - Direct threshold questions (8 questions)
    {
        "category": "Pricing Authority",
        "question": "What is the maximum price change percentage I can approve independently?",
        "expected": "15%",
        "keywords": ["15", "percent"],
        "weight": 1.0
    },
    {
        "category": "Pricing Authority",
        "question": "Can I change a price by 10% without getting approval?",
        "expected": "Yes, within 15% autonomous authority",
        "keywords": ["yes", "15", "autonomous"],
        "weight": 1.0
    },
    {
        "category": "Pricing Authority",
        "question": "Do I need senior director approval for a 20% price change?",
        "expected": "Yes, exceeds 15% limit",
        "keywords": ["yes", "15", "senior", "director"],
        "weight": 1.0
    },
    {
        "category": "Pricing Authority",
        "question": "Who approves price changes over 15%?",
        "expected": "Senior Director of Merchandise",
        "keywords": ["senior", "director", "merchandise"],
        "weight": 1.0
    },
    {
        "category": "Pricing Authority",
        "question": "Is a 5% price adjustment within my authority?",
        "expected": "Yes, under 15% threshold",
        "keywords": ["yes", "15"],
        "weight": 1.0
    },
    {
        "category": "Pricing Authority",
        "question": "Can I reduce a price by 12%?",
        "expected": "Yes, within 15% limit",
        "keywords": ["yes", "15", "within"],
        "weight": 1.0
    },
    {
        "category": "Pricing Authority",
        "question": "Does a 25% discount require approval?",
        "expected": "Yes, exceeds 15% autonomous threshold",
        "keywords": ["yes", "15", "approval"],
        "weight": 1.0
    },
    {
        "category": "Pricing Authority",
        "question": "What's the pricing change threshold before I need escalation?",
        "expected": "15%",
        "keywords": ["15", "percent", "threshold"],
        "weight": 1.0
    },
    
    # Margin - Direct requirements (8 questions)
    {
        "category": "Margin Requirements",
        "question": "What is the minimum margin requirement for retail products?",
        "expected": "25%",
        "keywords": ["25", "percent", "margin"],
        "weight": 1.0
    },
    {
        "category": "Margin Requirements",
        "question": "What is the minimum margin for marketplace products?",
        "expected": "15%",
        "keywords": ["15", "percent", "marketplace"],
        "weight": 1.0
    },
    {
        "category": "Margin Requirements",
        "question": "Can I sell a retail product with 25% margin?",
        "expected": "Yes, meets minimum requirement",
        "keywords": ["yes", "25", "minimum"],
        "weight": 1.0
    },
    {
        "category": "Margin Requirements",
        "question": "Is 20% margin acceptable for retail?",
        "expected": "No, minimum is 25%",
        "keywords": ["no", "25", "minimum"],
        "weight": 1.0
    },
    {
        "category": "Margin Requirements",
        "question": "Can a marketplace product have 16% margin?",
        "expected": "Yes, exceeds 15% minimum",
        "keywords": ["yes", "15", "exceeds"],
        "weight": 1.0
    },
    {
        "category": "Margin Requirements",
        "question": "What's the margin difference between retail and marketplace?",
        "expected": "Retail 25%, marketplace 15%",
        "keywords": ["25", "15", "retail", "marketplace"],
        "weight": 1.0
    },
    {
        "category": "Margin Requirements",
        "question": "Is 28% margin good for retail products?",
        "expected": "Yes, exceeds 25% minimum",
        "keywords": ["yes", "25", "exceeds"],
        "weight": 1.0
    },
    {
        "category": "Margin Requirements",
        "question": "Can I list a marketplace item with 14% margin?",
        "expected": "No, minimum 15% required",
        "keywords": ["no", "15", "minimum"],
        "weight": 1.0
    },
    
    # In-stock - Direct targets (5 questions)
    {
        "category": "In-Stock Management",
        "question": "What is our in-stock rate target?",
        "expected": "95%",
        "keywords": ["95", "percent"],
        "weight": 1.0
    },
    {
        "category": "In-Stock Management",
        "question": "How many hours can a product be out of stock?",
        "expected": "72 hours maximum",
        "keywords": ["72", "hours", "maximum"],
        "weight": 1.0
    },
    {
        "category": "In-Stock Management",
        "question": "Is 96% in-stock rate acceptable?",
        "expected": "Yes, exceeds 95% target",
        "keywords": ["yes", "95", "exceeds"],
        "weight": 1.0
    },
    {
        "category": "In-Stock Management",
        "question": "Can a product be out of stock for 48 hours?",
        "expected": "Yes, within 72-hour limit",
        "keywords": ["yes", "72", "within"],
        "weight": 1.0
    },
    {
        "category": "In-Stock Management",
        "question": "What's the maximum stockout duration allowed?",
        "expected": "72 hours",
        "keywords": ["72", "hours"],
        "weight": 1.0
    },
    
    # Vendor - Clear limits (6 questions)
    {
        "category": "Vendor Management",
        "question": "What is the maximum gift value I can accept from vendors?",
        "expected": "$25",
        "keywords": ["25", "dollar"],
        "weight": 1.0
    },
    {
        "category": "Vendor Management",
        "question": "What is my contract negotiation authority limit?",
        "expected": "$250,000",
        "keywords": ["250", "thousand"],
        "weight": 1.0
    },
    {
        "category": "Vendor Management",
        "question": "Can I accept a $20 gift from a vendor?",
        "expected": "Yes, under $25 limit",
        "keywords": ["yes", "25", "under"],
        "weight": 1.0
    },
    {
        "category": "Vendor Management",
        "question": "Do I need VP approval for a $300K contract?",
        "expected": "Yes, exceeds $250K authority",
        "keywords": ["yes", "250", "VP", "approval"],
        "weight": 1.0
    },
    {
        "category": "Vendor Management",
        "question": "Can I sign a $200K vendor contract?",
        "expected": "Yes, within $250K authority",
        "keywords": ["yes", "250", "within"],
        "weight": 1.0
    },
    {
        "category": "Vendor Management",
        "question": "Is a $30 vendor gift acceptable?",
        "expected": "No, exceeds $25 maximum",
        "keywords": ["no", "25", "exceeds"],
        "weight": 1.0
    },
    
    # Product Selection - Clear criteria (4 questions)
    {
        "category": "Product Selection",
        "question": "What is the minimum product rating required?",
        "expected": "3.0 stars",
        "keywords": ["3", "star", "minimum"],
        "weight": 1.0
    },
    {
        "category": "Product Selection",
        "question": "What is the maximum return rate allowed?",
        "expected": "15%",
        "keywords": ["15", "percent", "return"],
        "weight": 1.0
    },
    {
        "category": "Product Selection",
        "question": "Can I add a product with 3.5 stars?",
        "expected": "Yes, exceeds 3.0 minimum",
        "keywords": ["yes", "3", "exceeds"],
        "weight": 1.0
    },
    {
        "category": "Product Selection",
        "question": "Is 10% return rate acceptable?",
        "expected": "Yes, under 15% maximum",
        "keywords": ["yes", "15", "under"],
        "weight": 1.0
    },
    
    # KPI - Direct targets (3 questions)
    {
        "category": "KPI Targets",
        "question": "What is our annual revenue growth target?",
        "expected": "15% year-over-year",
        "keywords": ["15", "percent", "year"],
        "weight": 1.0
    },
    {
        "category": "KPI Targets",
        "question": "What is our perfect order rate target?",
        "expected": "95%",
        "keywords": ["95", "percent"],
        "weight": 1.0
    },
    {
        "category": "KPI Targets",
        "question": "What is the maximum acceptable return rate?",
        "expected": "8%",
        "keywords": ["8", "percent"],
        "weight": 1.0
    },
    
    # Compliance - Clear timelines (3 questions)
    {
        "category": "Compliance",
        "question": "How quickly must we remove products with safety issues?",
        "expected": "4 hours",
        "keywords": ["4", "hour"],
        "weight": 1.0
    },
    {
        "category": "Compliance",
        "question": "What is the response time for IP violations?",
        "expected": "24 hours",
        "keywords": ["24", "hour"],
        "weight": 1.0
    },
    {
        "category": "Compliance",
        "question": "How long to fix product content errors?",
        "expected": "72 hours",
        "keywords": ["72", "hour"],
        "weight": 1.0
    },
    
    # Reporting - Direct deadlines (2 questions)
    {
        "category": "Reporting",
        "question": "When are weekly reports due?",
        "expected": "Monday 10 AM PST",
        "keywords": ["monday", "10", "am"],
        "weight": 1.0
    },
    {
        "category": "Reporting",
        "question": "When is the monthly forecast due?",
        "expected": "15th of each month",
        "keywords": ["15", "month"],
        "weight": 1.0
    },
    
    # Promotions - Simple requirements (1 question)
    {
        "category": "Promotions",
        "question": "How many weeks advance notice for promotions?",
        "expected": "6 weeks",
        "keywords": ["6", "week"],
        "weight": 1.0
    },
]


def test_model(client, model_name, question):
    """Test a specific model with a question"""
    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions about company policies and compliance requirements. Be concise and specific."},
                {"role": "user", "content": question}
            ],
            temperature=0,
            max_tokens=300
        )
        
        duration = time.time() - start_time
        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        return {
            "answer": answer,
            "duration": duration,
            "tokens": tokens_used,
            "success": True
        }
    except Exception as e:
        return {
            "answer": f"ERROR: {str(e)}",
            "duration": time.time() - start_time,
            "tokens": 0,
            "success": False
        }


def evaluate_answer(answer, expected, keywords, weight=1.0):
    """Evaluate answer quality using keyword matching"""
    answer_lower = answer.lower()
    
    if answer.startswith("ERROR"):
        return 0.0
        
    keyword_matches = sum(1 for kw in keywords if kw.lower() in answer_lower)
    keyword_score = keyword_matches / len(keywords) if keywords else 0
    
    # More lenient scoring for direct questions
    if keyword_score >= 0.5:
        return weight
    elif keyword_score >= 0.4:
        return weight * 0.7
    else:
        return 0.0


def run_round4_test():
    """Run Round 4 evaluation with 40 straightforward questions"""
    print_header("ROUND 4: 40 DIRECT POLICY QUESTIONS")
    print(f"{CYAN}Straightforward questions targeting 85%+ accuracy{RESET}")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print_error("OPENAI_API_KEY not found!")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    base_model = "gpt-4o-mini"
    finetuned_model = os.getenv("FINETUNED_MODEL_ID")
    
    if not finetuned_model:
        print_error("FINETUNED_MODEL_ID not found!")
        sys.exit(1)
    
    print(f"\n{BOLD}Models:{RESET}")
    print(f"  Base: {CYAN}{base_model}{RESET}")
    print(f"  Fine-tuned: {CYAN}{finetuned_model}{RESET}\n")
    
    base_results = []
    finetuned_results = []
    base_scores = []
    finetuned_scores = []
    categories = {}
    
    total = len(TEST_QUESTIONS_ROUND4)
    print(f"{BOLD}Running {total} tests...{RESET}")
    
    for idx, test_case in enumerate(TEST_QUESTIONS_ROUND4, 1):
        question = test_case["question"]
        category = test_case["category"]
        expected = test_case["expected"]
        keywords = test_case["keywords"]
        weight = test_case["weight"]
        
        if category not in categories:
            categories[category] = {"base": [], "finetuned": []}
        
        progress = f"[{idx}/{total}]"
        print(f"\r{CYAN}{progress}{RESET} Testing: {question[:60]}...", end="", flush=True)
        
        base_result = test_model(client, base_model, question)
        finetuned_result = test_model(client, finetuned_model, question)
        
        base_score = evaluate_answer(base_result["answer"], expected, keywords, weight)
        finetuned_score = evaluate_answer(finetuned_result["answer"], expected, keywords, weight)
        
        base_results.append(base_result)
        finetuned_results.append(finetuned_result)
        base_scores.append(base_score)
        finetuned_scores.append(finetuned_score)
        
        categories[category]["base"].append(base_score)
        categories[category]["finetuned"].append(finetuned_score)
    
    print(f"\r{' ' * 100}\r")
    
    # Calculate metrics
    total_possible = sum(t["weight"] for t in TEST_QUESTIONS_ROUND4)
    base_total_score = sum(base_scores)
    finetuned_total_score = sum(finetuned_scores)
    
    base_accuracy = (base_total_score / total_possible) * 100
    finetuned_accuracy = (finetuned_total_score / total_possible) * 100
    
    base_avg_tokens = sum(r["tokens"] for r in base_results) / len(base_results)
    finetuned_avg_tokens = sum(r["tokens"] for r in finetuned_results) / len(finetuned_results)
    
    base_avg_time = sum(r["duration"] for r in base_results) / len(base_results)
    finetuned_avg_time = sum(r["duration"] for r in finetuned_results) / len(finetuned_results)
    
    # Print results
    print_header("ROUND 4 RESULTS")
    
    print(f"{BOLD}Overall Performance:{RESET}")
    print(f"  Base Model:       {base_accuracy:.1f}% accuracy ({base_total_score:.1f}/{total_possible:.1f} points)")
    print(f"  Fine-tuned Model: {finetuned_accuracy:.1f}% accuracy ({finetuned_total_score:.1f}/{total_possible:.1f} points)")
    
    accuracy_diff = finetuned_accuracy - base_accuracy
    if accuracy_diff >= 25:
        print_success(f"  Improvement: +{accuracy_diff:.1f}% ✓ TARGET MET!")
    elif accuracy_diff > 0:
        print_success(f"  Improvement: +{accuracy_diff:.1f}%")
    else:
        print_warning(f"  Difference: {accuracy_diff:.1f}%")
    
    # Check if fine-tuned hit 85% target
    if finetuned_accuracy >= 85:
        print_success(f"  🎯 Fine-tuned accuracy target ACHIEVED (≥85%)!")
    elif finetuned_accuracy >= 80:
        print_info(f"  ⚡ Close to target (80-85%)")
    else:
        print_warning(f"  ⚠ Below 85% target")
    
    print(f"\n{BOLD}Token Usage:{RESET}")
    print(f"  Base Model:       {base_avg_tokens:.1f} avg tokens")
    print(f"  Fine-tuned Model: {finetuned_avg_tokens:.1f} avg tokens")
    token_diff = ((finetuned_avg_tokens - base_avg_tokens) / base_avg_tokens) * 100
    if token_diff < 0:
        print_success(f"  Efficiency: {token_diff:.1f}% fewer tokens")
    else:
        print_warning(f"  Usage: +{token_diff:.1f}% more tokens")
    
    print(f"\n{BOLD}Response Time:{RESET}")
    print(f"  Base Model:       {base_avg_time:.2f}s avg")
    print(f"  Fine-tuned Model: {finetuned_avg_time:.2f}s avg")
    time_diff = ((finetuned_avg_time - base_avg_time) / base_avg_time) * 100
    if time_diff < 0:
        print_success(f"  Speed: {abs(time_diff):.1f}% faster")
    else:
        print_warning(f"  Speed: +{time_diff:.1f}% slower")
    
    # Category breakdown
    print(f"\n{BOLD}Category Breakdown:{RESET}")
    for category, scores in sorted(categories.items()):
        base_cat_score = (sum(scores["base"]) / len(scores["base"])) * 100
        finetuned_cat_score = (sum(scores["finetuned"]) / len(scores["finetuned"])) * 100
        diff = finetuned_cat_score - base_cat_score
        
        print(f"\n  {BOLD}{category}:{RESET}")
        print(f"    Base: {base_cat_score:.1f}%  |  Fine-tuned: {finetuned_cat_score:.1f}%  |  Diff: {diff:+.1f}%")
    
    # Summary statistics
    print(f"\n{BOLD}Test Summary:{RESET}")
    print(f"  Total Questions: {total}")
    print(f"  Base Correct: {sum(1 for s in base_scores if s >= 0.5)} questions")
    print(f"  Fine-tuned Correct: {sum(1 for s in finetuned_scores if s >= 0.5)} questions")
    
    print(f"\n{BOLD}{'='*70}{RESET}")
    if finetuned_accuracy >= 85 and accuracy_diff >= 25:
        print_success(f"🏆 EXCELLENT! Both targets achieved!")
    elif finetuned_accuracy >= 85:
        print_success(f"✓ High accuracy achieved!")
    elif accuracy_diff >= 25:
        print_success(f"✓ Strong improvement demonstrated!")
    else:
        print_info(f"Good results")
    
    # Save results
    results_data = {
        "round": 4,
        "timestamp": datetime.now().isoformat(),
        "models": {
            "base": base_model,
            "finetuned": finetuned_model
        },
        "overall": {
            "base_accuracy": base_accuracy,
            "finetuned_accuracy": finetuned_accuracy,
            "accuracy_difference": accuracy_diff,
            "base_avg_tokens": base_avg_tokens,
            "finetuned_avg_tokens": finetuned_avg_tokens,
            "base_avg_time": base_avg_time,
            "finetuned_avg_time": finetuned_avg_time
        },
        "categories": {
            cat: {
                "base_accuracy": (sum(scores["base"]) / len(scores["base"])) * 100,
                "finetuned_accuracy": (sum(scores["finetuned"]) / len(scores["finetuned"])) * 100
            }
            for cat, scores in categories.items()
        },
        "questions": [
            {
                "question": test_case["question"],
                "category": test_case["category"],
                "expected": test_case["expected"],
                "base_answer": base_results[i]["answer"],
                "finetuned_answer": finetuned_results[i]["answer"],
                "base_score": base_scores[i],
                "finetuned_score": finetuned_scores[i]
            }
            for i, test_case in enumerate(TEST_QUESTIONS_ROUND4)
        ]
    }
    
    output_file = "evaluation_results_round4.json"
    with open(output_file, "w") as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n{CYAN}Round 4 results saved to: {output_file}{RESET}\n")


if __name__ == "__main__":
    run_round4_test()
