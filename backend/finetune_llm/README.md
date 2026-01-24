# QLoRA Fine-Tuning for Policy Compliance LLM

This directory contains scripts and configuration for fine-tuning LLMs using QLoRA (Quantized Low-Rank Adaptation) for the policy compliance domain.

## Directory Structure

```
finetune_llm/
├── README.md                    # This file
├── requirements.txt             # Dependencies for fine-tuning
├── config/
│   └── qlora_config.yaml        # Training configuration
├── scripts/
│   ├── generate_training_data.py    # Generate Q&A pairs from policies
│   ├── finetune_qlora.py            # Main QLoRA training script
│   ├── merge_adapter.py             # Merge LoRA adapter with base model
│   └── convert_to_ollama.py         # Convert to Ollama format
├── data/
│   ├── raw/                     # Raw training data
│   └── processed/               # Processed datasets
└── outputs/
    ├── adapters/                # Trained LoRA adapters
    ├── merged/                  # Merged full models
    └── gguf/                    # GGUF quantized models
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Training Data
```bash
python scripts/generate_training_data.py --docs_dir ../../sample_docs --output data/processed/training_data.jsonl
```

### 3. Run QLoRA Fine-Tuning
```bash
python scripts/finetune_qlora.py --config config/qlora_config.yaml
```

### 4. Merge and Export
```bash
python scripts/merge_adapter.py --adapter outputs/adapters/policy-llama --output outputs/merged/policy-llama-merged
python scripts/convert_to_ollama.py --model outputs/merged/policy-llama-merged --name policy-compliance-llm
```

## Hardware Requirements

| GPU VRAM | Recommended Model |
|----------|-------------------|
| 8GB      | Llama 3.1 8B (4-bit) |
| 16GB     | Llama 3.1 8B (4-bit) + larger batch |
| 24GB+    | Llama 3.1 8B/70B options |

## Training Configuration

See `config/qlora_config.yaml` for all training parameters including:
- LoRA rank and alpha
- Quantization settings (4-bit NF4)
- Learning rate and scheduler
- Batch size and gradient accumulation

## Expected Results

After fine-tuning on policy documents:
- ~15-25% improvement on compliance Q&A accuracy
- Better policy citation and reference
- Domain-specific terminology understanding
- Reduced hallucination on policy details
