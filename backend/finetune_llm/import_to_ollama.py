"""
Import GGUF model to Ollama
Creates Modelfile and imports the fine-tuned model
"""

import os
import subprocess

print("=" * 60)
print("Importing to Ollama")
print("=" * 60)

GGUF_FILE = "./policy-compliance-llm-Q4_K_M.gguf"
MODEL_NAME = "policy-compliance-llm"
MODELFILE = "./Modelfile"

# Check GGUF exists
if not os.path.exists(GGUF_FILE):
    print(f"❌ Error: GGUF not found at {GGUF_FILE}")
    print("Run convert_to_gguf.py first")
    exit(1)

# Create Modelfile
print(f"\n[1/2] Creating Modelfile...")
modelfile_content = f"""FROM ./{os.path.basename(GGUF_FILE)}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40

SYSTEM You are a helpful AI assistant specialized in company policy compliance. You provide accurate, context-aware answers about employee policies, leave policies, remote work guidelines, data privacy, security protocols, and NDAs. Always cite specific policy sections when relevant.

TEMPLATE \"\"\"{{{{ if .System }}}}<|start_header_id|>system<|end_header_id|>

{{{{ .System }}}}<|eot_id|>{{{{ end }}}}{{{{ if .Prompt }}}}<|start_header_id|>user<|end_header_id|>

{{{{ .Prompt }}}}<|eot_id|>{{{{ end }}}}<|start_header_id|>assistant<|end_header_id|>

{{{{ .Response }}}}<|eot_id|>\"\"\"
"""

with open(MODELFILE, 'w') as f:
    f.write(modelfile_content)
print(f"✅ Modelfile created")

# Import to Ollama
print(f"\n[2/2] Importing to Ollama as '{MODEL_NAME}'...")
print("      (This takes 1-2 minutes)")
result = subprocess.run([
    "ollama", "create", MODEL_NAME, "-f", MODELFILE
], capture_output=True, text=True)

if result.returncode == 0:
    print(f"✅ Model imported successfully")
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Model ready to use")
    print("=" * 60)
    print(f"\nTest it with:")
    print(f"  ollama run {MODEL_NAME}")
    print(f"\nExample questions:")
    print(f'  "How many vacation days do employees get?"')
    print(f'  "What are the remote work eligibility requirements?"')
    print(f'  "Can I share confidential information with contractors?"')
    
else:
    print(f"❌ Error importing to Ollama:")
    print(result.stderr)
    exit(1)
