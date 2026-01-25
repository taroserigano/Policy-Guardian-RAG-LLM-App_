# Fine-tuned Model Import Guide

## Prerequisites
- 16GB+ RAM (you have 64GB ✓)
- Python packages: `transformers`, `peft`, `torch`
- CMake (for building llama.cpp quantizer)
- Git

## Step-by-Step Process

### 1. Download Adapter from Google Drive
1. Go to Google Drive (your new account)
2. Navigate to: `MyDrive/policy-llama/final/`
3. Download all files to: `backend/finetune_llm/policy-llama-adapter/`

Expected files:
- adapter_config.json
- adapter_model.safetensors
- tokenizer.json
- tokenizer_config.json
- special_tokens_map.json
- chat_template.jinja

### 2. Install Requirements
```bash
pip install transformers peft torch sentencepiece
```

Install CMake from: https://cmake.org/download/ (if not installed)

### 3. Merge Adapter with Base Model
```bash
cd backend/finetune_llm
python merge_adapter.py
```
**Time:** ~10-15 minutes
**Output:** `policy-llama-merged/` directory (~16GB)

### 4. Convert to GGUF
```bash
python convert_to_gguf.py
```
**Time:** ~15-20 minutes
**Output:** `policy-compliance-llm-Q4_K_M.gguf` (~5GB)

### 5. Import to Ollama
```bash
python import_to_ollama.py
```
**Time:** ~2 minutes
**Result:** Model available as `policy-compliance-llm` in Ollama

### 6. Test the Model
```bash
ollama run policy-compliance-llm
```

Example prompts:
- "How many vacation days do employees get?"
- "What are the remote work eligibility requirements?"
- "Can I share confidential information with contractors?"

## Troubleshooting

**CMake not found:**
- Install from: https://cmake.org/download/
- Add to PATH during installation

**Out of memory during merge:**
- Close other applications
- Your 64GB should be sufficient

**Ollama not recognized:**
- Make sure Ollama is running: `start.bat`
- Check Ollama service is active on port 11434

## Total Time Estimate
- Download adapter: 5-10 min (depends on internet)
- Merge: 10-15 min
- Convert to GGUF: 15-20 min
- Import to Ollama: 2 min
- **Total: ~30-45 minutes**
