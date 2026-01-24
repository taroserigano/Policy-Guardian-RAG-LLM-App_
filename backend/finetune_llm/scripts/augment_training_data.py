"""
Data Augmentation Script for QLoRA Training Data

This script expands the training dataset by:
1. Generating paraphrased versions of existing Q&A pairs
2. Creating multi-turn conversation examples
3. Adding negative/edge case examples
4. Generating comparative questions

Usage:
    python augment_training_data.py --input ../data/processed/training_data.jsonl --output ../data/processed/training_data_augmented.jsonl
"""

import os
import json
import argparse
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict
import random

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")


async def call_ollama(prompt: str, system_prompt: str = None) -> str:
    """Call Ollama API."""
    async with httpx.AsyncClient(timeout=180.0) as client:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.8, "num_predict": 512}
            }
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


async def paraphrase_question(question: str) -> str:
    """Generate a paraphrased version of a question."""
    prompt = f"""Paraphrase this question while keeping the same meaning. Return ONLY the paraphrased question, nothing else.

Original: {question}

Paraphrased:"""
    
    return (await call_ollama(prompt)).strip()


async def create_follow_up(question: str, answer: str) -> Dict[str, str]:
    """Create a follow-up question based on the answer."""
    prompt = f"""Based on this Q&A, create a natural follow-up question and answer.

Original Question: {question}
Original Answer: {answer}

Create a follow-up question that asks for more details, clarification, or a related aspect.
Return as JSON: {{"question": "...", "answer": "..."}}"""

    try:
        response = await call_ollama(prompt)
        # Extract JSON
        import re
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    return None


async def create_negative_example(question: str, answer: str, source: str) -> Dict[str, str]:
    """Create a compliance violation scenario."""
    prompt = f"""Based on this policy Q&A, create a scenario where someone violates the policy and explain why it's wrong.

Policy Question: {question}
Policy Answer: {answer}

Create a scenario showing INCORRECT behavior and why it violates the policy.
Return as JSON: {{"question": "Is this action compliant: [describe wrong action]?", "answer": "No, this is NOT compliant because..."}}"""

    try:
        response = await call_ollama(prompt)
        import re
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            result["source"] = source
            result["type"] = "negative_example"
            return result
    except:
        pass
    return None


async def create_comparative_question(items: List[Dict]) -> Dict[str, str]:
    """Create a question comparing different policies."""
    if len(items) < 2:
        return None
    
    item1, item2 = random.sample(items, 2)
    
    prompt = f"""Create a question that compares these two policy areas:

Policy 1 ({item1.get('source', 'Policy A')}): {item1.get('question', '')[:200]}
Policy 2 ({item2.get('source', 'Policy B')}): {item2.get('question', '')[:200]}

Create a comparative question and comprehensive answer.
Return as JSON: {{"question": "...", "answer": "..."}}"""

    try:
        response = await call_ollama(prompt)
        import re
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            result["type"] = "comparative"
            return result
    except:
        pass
    return None


async def augment_dataset(input_file: str, output_file: str, target_size: int = 800):
    """Augment the training dataset."""
    
    # Load existing data
    print(f"Loading data from {input_file}...")
    data = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    original_count = len(data)
    print(f"Original examples: {original_count}")
    print(f"Target size: {target_size}")
    
    augmented = list(data)  # Start with original data
    
    # Calculate how many to generate
    needed = target_size - original_count
    if needed <= 0:
        print("Already at target size!")
        return
    
    print(f"\nGenerating {needed} additional examples...")
    
    # Strategy: Mix of different augmentation types
    paraphrase_count = needed // 3
    follow_up_count = needed // 3
    negative_count = needed // 4
    comparative_count = needed - paraphrase_count - follow_up_count - negative_count
    
    generated = 0
    
    # 1. Paraphrase existing questions
    print(f"\n1. Generating {paraphrase_count} paraphrased questions...")
    sample_for_paraphrase = random.sample(data, min(paraphrase_count, len(data)))
    
    for i, item in enumerate(sample_for_paraphrase):
        try:
            new_q = await paraphrase_question(item.get('question', item.get('instruction', '')))
            if new_q and len(new_q) > 10:
                augmented.append({
                    "question": new_q,
                    "answer": item.get('answer', item.get('output', '')),
                    "source": item.get('source', ''),
                    "type": "paraphrase"
                })
                generated += 1
                print(f"  [{generated}/{needed}] Paraphrased: {new_q[:50]}...")
        except Exception as e:
            print(f"  Error: {e}")
        
        if generated >= paraphrase_count:
            break
        await asyncio.sleep(0.3)
    
    # 2. Generate follow-up questions
    print(f"\n2. Generating {follow_up_count} follow-up questions...")
    sample_for_followup = random.sample(data, min(follow_up_count, len(data)))
    
    for item in sample_for_followup:
        try:
            follow_up = await create_follow_up(
                item.get('question', item.get('instruction', '')),
                item.get('answer', item.get('output', ''))
            )
            if follow_up and follow_up.get('question') and follow_up.get('answer'):
                follow_up['source'] = item.get('source', '')
                follow_up['type'] = 'follow_up'
                augmented.append(follow_up)
                generated += 1
                print(f"  [{generated}/{needed}] Follow-up: {follow_up['question'][:50]}...")
        except Exception as e:
            print(f"  Error: {e}")
        
        if generated >= paraphrase_count + follow_up_count:
            break
        await asyncio.sleep(0.3)
    
    # 3. Generate negative examples
    print(f"\n3. Generating {negative_count} negative/violation examples...")
    sample_for_negative = random.sample(data, min(negative_count, len(data)))
    
    for item in sample_for_negative:
        try:
            negative = await create_negative_example(
                item.get('question', item.get('instruction', '')),
                item.get('answer', item.get('output', '')),
                item.get('source', '')
            )
            if negative and negative.get('question') and negative.get('answer'):
                augmented.append(negative)
                generated += 1
                print(f"  [{generated}/{needed}] Negative: {negative['question'][:50]}...")
        except Exception as e:
            print(f"  Error: {e}")
        
        if generated >= paraphrase_count + follow_up_count + negative_count:
            break
        await asyncio.sleep(0.3)
    
    # 4. Generate comparative questions
    print(f"\n4. Generating {comparative_count} comparative questions...")
    for _ in range(comparative_count):
        try:
            comparative = await create_comparative_question(data)
            if comparative and comparative.get('question') and comparative.get('answer'):
                augmented.append(comparative)
                generated += 1
                print(f"  [{generated}/{needed}] Comparative: {comparative['question'][:50]}...")
        except Exception as e:
            print(f"  Error: {e}")
        await asyncio.sleep(0.3)
    
    # Save augmented dataset
    print(f"\n\nSaving augmented dataset...")
    
    # Save raw format
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in augmented:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Save alpaca format
    alpaca_file = output_file.replace('.jsonl', '.alpaca.jsonl')
    with open(alpaca_file, 'w', encoding='utf-8') as f:
        for item in augmented:
            alpaca = {
                "instruction": item.get('question', item.get('instruction', '')),
                "input": "",
                "output": item.get('answer', item.get('output', '')),
                "source": item.get('source', ''),
                "type": item.get('type', 'original')
            }
            f.write(json.dumps(alpaca, ensure_ascii=False) + '\n')
    
    # Save chat format
    chat_file = output_file.replace('.jsonl', '.chat.jsonl')
    system_msg = "You are a compliance assistant specializing in corporate policies. You provide accurate, helpful answers about policy requirements, procedures, and best practices."
    with open(chat_file, 'w', encoding='utf-8') as f:
        for item in augmented:
            chat = {
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": item.get('question', item.get('instruction', ''))},
                    {"role": "assistant", "content": item.get('answer', item.get('output', ''))}
                ],
                "source": item.get('source', ''),
                "type": item.get('type', 'original')
            }
            f.write(json.dumps(chat, ensure_ascii=False) + '\n')
    
    print(f"\n{'='*60}")
    print(f"Augmentation Complete!")
    print(f"{'='*60}")
    print(f"Original examples: {original_count}")
    print(f"New examples generated: {generated}")
    print(f"Total examples: {len(augmented)}")
    print(f"\nFiles saved:")
    print(f"  - {output_file}")
    print(f"  - {alpaca_file}")
    print(f"  - {chat_file}")


async def main():
    parser = argparse.ArgumentParser(description="Augment QLoRA training data")
    parser.add_argument("--input", type=str, default="../data/processed/training_data.jsonl")
    parser.add_argument("--output", type=str, default="../data/processed/training_data_augmented.jsonl")
    parser.add_argument("--target", type=int, default=800, help="Target dataset size")
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    input_file = (script_dir / args.input).resolve()
    output_file = (script_dir / args.output).resolve()
    
    await augment_dataset(str(input_file), str(output_file), args.target)


if __name__ == "__main__":
    asyncio.run(main())
