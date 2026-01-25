"""
Merge LoRA adapter with base Llama model locally
Requires: 16GB+ RAM, downloaded adapter in ./policy-llama-adapter/
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os

print("=" * 60)
print("Merging LoRA Adapter with Base Model")
print("=" * 60)

# Paths
ADAPTER_PATH = "./policy-llama/final"
OUTPUT_PATH = "./policy-llama-merged"
BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"

# Check adapter exists
if not os.path.exists(ADAPTER_PATH):
    print(f"❌ Error: Adapter not found at {ADAPTER_PATH}")
    print(f"Please download from Google Drive to this location")
    exit(1)

print(f"\n📂 Adapter path: {ADAPTER_PATH}")
print(f"📂 Output path: {OUTPUT_PATH}")
print(f"🤖 Base model: {BASE_MODEL}")

# Load base model
print(f"\n[1/4] Loading base model from HuggingFace...")
print("      (This downloads ~16GB, takes 5-10 min on first run)")
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    device_map="cpu",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
)
print("✅ Base model loaded")

# Load adapter
print(f"\n[2/4] Loading LoRA adapter...")
model_with_adapter = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
print("✅ Adapter loaded")

# Merge
print(f"\n[3/4] Merging adapter into base model...")
print("      (This takes 2-5 minutes)")
merged_model = model_with_adapter.merge_and_unload()
print("✅ Merge complete")

# Save merged model
print(f"\n[4/4] Saving merged model to {OUTPUT_PATH}...")
os.makedirs(OUTPUT_PATH, exist_ok=True)
merged_model.save_pretrained(OUTPUT_PATH, safe_serialization=True)

# Save tokenizer
tokenizer = AutoTokenizer.from_pretrained(ADAPTER_PATH)
tokenizer.save_pretrained(OUTPUT_PATH)
print("✅ Model and tokenizer saved")

print("\n" + "=" * 60)
print("✅ SUCCESS! Merged model saved to:")
print(f"   {os.path.abspath(OUTPUT_PATH)}")
print("=" * 60)
print("\nNext step: Run convert_to_gguf.py to create GGUF for Ollama")
