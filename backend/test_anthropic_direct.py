"""
Test Anthropic API directly to diagnose the issue
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"API Key present: {bool(api_key)}")
print(f"API Key length: {len(api_key) if api_key else 0}")

if not api_key:
    print("ERROR: No API key found!")
    exit(1)

# Test different model names
models_to_test = [
    "claude-3-sonnet-20240229",
    "claude-3-5-sonnet-20241022", 
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307"
]

for model in models_to_test:
    print(f"\n{'='*70}")
    print(f"Testing model: {model}")
    print(f"{'='*70}")
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say 'hi' in one word"}],
                "max_tokens": 10
            },
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS! Response: {result['content'][0]['text']}")
            print(f"This model works: {model}")
            break
        else:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Exception: {e}")
