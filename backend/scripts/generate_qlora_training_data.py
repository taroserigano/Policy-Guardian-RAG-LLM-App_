"""
QLoRA Training Data Generator for Policy Compliance Domain

This script generates high-quality training data from policy documents
for fine-tuning LLMs on compliance-specific tasks.

Usage:
    python generate_qlora_training_data.py --docs_dir ../sample_docs --output ../training_data/qlora_dataset.jsonl
"""

import os
import json
import argparse
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import re


# Ollama API settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")


async def call_ollama(prompt: str, system_prompt: str = None, retries: int = 3) -> str:
    """Call Ollama API for text generation with retry logic."""
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout
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
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 1024  # Reduced for faster responses
                        }
                    }
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception as e:
            if attempt < retries - 1:
                print(f"    Retry {attempt + 1}/{retries} after error: {e}")
                await asyncio.sleep(2)
            else:
                raise
    return ""


def chunk_document(text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
    """Split document into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to end at a sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            if break_point > chunk_size // 2:
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return [c for c in chunks if len(c) > 100]  # Filter tiny chunks


async def generate_qa_pairs(chunk: str, doc_name: str, num_pairs: int = 3) -> List[Dict[str, str]]:
    """Generate Q&A pairs from a document chunk."""
    
    system_prompt = """You are a compliance training data generator. Your task is to create 
high-quality question-answer pairs from policy documents. The questions should be:
- Practical and workplace-relevant
- Varied in complexity (some simple, some requiring reasoning)
- Focused on policy compliance, procedures, and requirements

Format your response as a JSON array with objects containing "question" and "answer" keys.
Make answers comprehensive but concise, citing specific policy requirements when relevant."""

    prompt = f"""Based on this excerpt from "{doc_name}", generate exactly {num_pairs} diverse question-answer pairs.

POLICY EXCERPT:
{chunk}

Generate questions that cover:
1. Direct policy requirements (what must/should be done)
2. Scenarios and edge cases (what to do in specific situations)  
3. Compliance verification (how to ensure/check compliance)

Return ONLY a valid JSON array like:
[
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}}
]"""

    try:
        response = await call_ollama(prompt, system_prompt)
        
        # Extract JSON from response
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            pairs = json.loads(json_match.group())
            # Validate structure
            valid_pairs = []
            for p in pairs:
                if isinstance(p, dict) and "question" in p and "answer" in p:
                    valid_pairs.append({
                        "question": p["question"].strip(),
                        "answer": p["answer"].strip(),
                        "source": doc_name
                    })
            return valid_pairs
    except Exception as e:
        print(f"  Warning: Failed to generate pairs: {e}")
    
    return []


async def generate_compliance_scenarios(chunk: str, doc_name: str) -> List[Dict[str, str]]:
    """Generate compliance scenario-based training data."""
    
    system_prompt = """You are a compliance training expert. Create realistic workplace scenarios 
that test understanding of policy requirements. Each scenario should present a situation 
and ask what the correct action should be according to policy."""

    prompt = f"""Based on this policy excerpt from "{doc_name}", create 2 realistic compliance scenarios.

POLICY EXCERPT:
{chunk}

For each scenario, provide:
1. A realistic workplace situation involving this policy
2. A question asking what should be done
3. The correct answer based on the policy

Return as JSON array:
[
  {{"scenario": "...", "question": "...", "answer": "..."}},
  {{"scenario": "...", "question": "...", "answer": "..."}}
]"""

    try:
        response = await call_ollama(prompt, system_prompt)
        
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            scenarios = json.loads(json_match.group())
            valid_scenarios = []
            for s in scenarios:
                if isinstance(s, dict) and all(k in s for k in ["scenario", "question", "answer"]):
                    # Convert to instruction format
                    instruction = f"Scenario: {s['scenario']}\n\nQuestion: {s['question']}"
                    valid_scenarios.append({
                        "question": instruction,
                        "answer": s["answer"].strip(),
                        "source": doc_name,
                        "type": "scenario"
                    })
            return valid_scenarios
    except Exception as e:
        print(f"  Warning: Failed to generate scenarios: {e}")
    
    return []


async def generate_classification_examples(chunk: str, doc_name: str) -> List[Dict[str, str]]:
    """Generate compliance classification training data."""
    
    system_prompt = """You are a compliance analyst. Create examples where given a statement 
or action, you classify whether it's compliant or non-compliant with policy, and explain why."""

    prompt = f"""Based on this policy excerpt from "{doc_name}", create 2 compliance classification examples.

POLICY EXCERPT:
{chunk}

For each example:
1. Describe an action or statement
2. Classify as COMPLIANT or NON-COMPLIANT
3. Explain the reasoning based on policy

Return as JSON array:
[
  {{"action": "...", "classification": "COMPLIANT|NON-COMPLIANT", "reasoning": "..."}},
  {{"action": "...", "classification": "COMPLIANT|NON-COMPLIANT", "reasoning": "..."}}
]"""

    try:
        response = await call_ollama(prompt, system_prompt)
        
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            examples = json.loads(json_match.group())
            valid_examples = []
            for e in examples:
                if isinstance(e, dict) and all(k in e for k in ["action", "classification", "reasoning"]):
                    question = f"Analyze the following action for policy compliance:\n\n{e['action']}\n\nIs this action compliant with {doc_name.replace('_', ' ').replace('.txt', '')}?"
                    answer = f"Classification: {e['classification']}\n\nReasoning: {e['reasoning']}"
                    valid_examples.append({
                        "question": question,
                        "answer": answer,
                        "source": doc_name,
                        "type": "classification"
                    })
            return valid_examples
    except Exception as e:
        print(f"  Warning: Failed to generate classification examples: {e}")
    
    return []


def convert_to_training_format(data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Convert Q&A pairs to various training formats."""
    
    formatted_data = []
    
    for item in data:
        # Alpaca format (most common for fine-tuning)
        alpaca_format = {
            "instruction": item["question"],
            "input": "",
            "output": item["answer"],
            "source": item.get("source", ""),
            "type": item.get("type", "qa")
        }
        formatted_data.append(alpaca_format)
        
    return formatted_data


def convert_to_chat_format(data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Convert to chat/conversation format for chat models."""
    
    formatted_data = []
    
    system_message = """You are a compliance assistant specializing in corporate policies. 
You provide accurate, helpful answers about policy requirements, procedures, and best practices. 
Always cite specific policy requirements when applicable."""
    
    for item in data:
        chat_format = {
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": item["question"]},
                {"role": "assistant", "content": item["answer"]}
            ],
            "source": item.get("source", ""),
            "type": item.get("type", "qa")
        }
        formatted_data.append(chat_format)
        
    return formatted_data


async def process_document(doc_path: Path) -> List[Dict[str, str]]:
    """Process a single document and generate training data."""
    
    print(f"\nProcessing: {doc_path.name}")
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chunks = chunk_document(content)
    print(f"  Split into {len(chunks)} chunks")
    
    all_pairs = []
    
    for i, chunk in enumerate(chunks):
        print(f"  Processing chunk {i+1}/{len(chunks)}...")
        
        # Generate different types of training data
        qa_pairs = await generate_qa_pairs(chunk, doc_path.name, num_pairs=3)
        all_pairs.extend(qa_pairs)
        print(f"    Generated {len(qa_pairs)} Q&A pairs")
        
        scenarios = await generate_compliance_scenarios(chunk, doc_path.name)
        all_pairs.extend(scenarios)
        print(f"    Generated {len(scenarios)} scenarios")
        
        classifications = await generate_classification_examples(chunk, doc_path.name)
        all_pairs.extend(classifications)
        print(f"    Generated {len(classifications)} classification examples")
        
        # Small delay to avoid overwhelming Ollama
        await asyncio.sleep(0.5)
    
    print(f"  Total pairs from {doc_path.name}: {len(all_pairs)}")
    return all_pairs


async def main():
    parser = argparse.ArgumentParser(description="Generate QLoRA training data from policy documents")
    parser.add_argument("--docs_dir", type=str, default="../sample_docs", 
                        help="Directory containing policy documents")
    parser.add_argument("--output", type=str, default="../training_data/qlora_dataset.jsonl",
                        help="Output JSONL file path")
    parser.add_argument("--format", type=str, choices=["alpaca", "chat", "both"], default="both",
                        help="Output format for training data")
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    docs_dir = (script_dir / args.docs_dir).resolve()
    output_path = (script_dir / args.output).resolve()
    
    print("=" * 60)
    print("QLoRA Training Data Generator")
    print("=" * 60)
    print(f"Documents directory: {docs_dir}")
    print(f"Output file: {output_path}")
    print(f"Output format: {args.format}")
    print(f"Ollama model: {OLLAMA_MODEL}")
    print("=" * 60)
    
    # Check Ollama availability
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            models = [m["name"] for m in response.json().get("models", [])]
            print(f"Available Ollama models: {', '.join(models)}")
            if OLLAMA_MODEL not in models and not any(OLLAMA_MODEL in m for m in models):
                print(f"Warning: {OLLAMA_MODEL} may not be available")
    except Exception as e:
        print(f"Error: Cannot connect to Ollama at {OLLAMA_BASE_URL}: {e}")
        return
    
    # Find all text documents
    doc_files = list(docs_dir.glob("*.txt")) + list(docs_dir.glob("*.md"))
    
    if not doc_files:
        print(f"Error: No .txt or .md files found in {docs_dir}")
        return
    
    print(f"\nFound {len(doc_files)} documents to process")
    
    # Process all documents
    all_training_data = []
    
    for doc_path in doc_files:
        pairs = await process_document(doc_path)
        all_training_data.extend(pairs)
    
    print("\n" + "=" * 60)
    print(f"Total raw training examples: {len(all_training_data)}")
    
    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save in requested format(s)
    if args.format in ["alpaca", "both"]:
        alpaca_data = convert_to_training_format(all_training_data)
        alpaca_path = output_path.with_suffix('.alpaca.jsonl')
        with open(alpaca_path, 'w', encoding='utf-8') as f:
            for item in alpaca_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Saved Alpaca format: {alpaca_path} ({len(alpaca_data)} examples)")
    
    if args.format in ["chat", "both"]:
        chat_data = convert_to_chat_format(all_training_data)
        chat_path = output_path.with_suffix('.chat.jsonl')
        with open(chat_path, 'w', encoding='utf-8') as f:
            for item in chat_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Saved Chat format: {chat_path} ({len(chat_data)} examples)")
    
    # Also save raw format
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in all_training_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"Saved raw format: {output_path} ({len(all_training_data)} examples)")
    
    # Print summary statistics
    print("\n" + "=" * 60)
    print("Summary Statistics")
    print("=" * 60)
    
    by_source = {}
    by_type = {}
    for item in all_training_data:
        source = item.get("source", "unknown")
        type_ = item.get("type", "qa")
        by_source[source] = by_source.get(source, 0) + 1
        by_type[type_] = by_type.get(type_, 0) + 1
    
    print("\nBy Document:")
    for source, count in sorted(by_source.items()):
        print(f"  {source}: {count} examples")
    
    print("\nBy Type:")
    for type_, count in sorted(by_type.items()):
        print(f"  {type_}: {count} examples")
    
    print("\n" + "=" * 60)
    print("Training data generation complete!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"1. Review the generated data in {output_path}")
    print(f"2. Run the QLoRA fine-tuning script:")
    print(f"   python finetune_qlora.py --data {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
