"""Quick HuggingFace login script"""
from huggingface_hub import login
import sys

print("Paste your HuggingFace token and press Enter:")
token = input().strip()

print("Logging in...")
login(token=token, add_to_git_credential=True)
print("✅ Login successful!")
