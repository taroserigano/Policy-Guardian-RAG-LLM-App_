"""
Merge LoRA Adapter with Base Model

This script merges the trained LoRA adapter weights back into the base model
to create a standalone fine-tuned model.

Usage:
    python merge_adapter.py --adapter ../outputs/adapters/policy-llama/final --output ../outputs/merged/policy-llama
"""

import os
import argparse
import logging
from pathlib import Path

import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def merge_lora_adapter(
    adapter_path: str,
    output_path: str,
    base_model: str = None,
    push_to_hub: bool = False,
    hub_model_id: str = None,
):
    """
    Merge LoRA adapter with base model.
    
    Args:
        adapter_path: Path to the trained LoRA adapter
        output_path: Path to save the merged model
        base_model: Base model ID (auto-detected from adapter config if not provided)
        push_to_hub: Whether to push to HuggingFace Hub
        hub_model_id: HuggingFace Hub model ID
    """
    logger.info("=" * 60)
    logger.info("Merging LoRA Adapter with Base Model")
    logger.info("=" * 60)
    
    adapter_path = Path(adapter_path)
    output_path = Path(output_path)
    
    # Load training config to get base model
    config_path = adapter_path / "training_config.yaml"
    if config_path.exists() and not base_model:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        base_model = config.get('model', {}).get('base_model')
        logger.info(f"Detected base model from config: {base_model}")
    
    if not base_model:
        raise ValueError("Base model not specified and could not be auto-detected. Use --base_model argument.")
    
    logger.info(f"Adapter path: {adapter_path}")
    logger.info(f"Base model: {base_model}")
    logger.info(f"Output path: {output_path}")
    
    # Load base model (in full precision for merging)
    logger.info("\n1. Loading base model...")
    base_model_instance = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    
    # Load tokenizer
    logger.info("2. Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        adapter_path,
        trust_remote_code=True,
    )
    
    # Load and merge LoRA adapter
    logger.info("3. Loading LoRA adapter...")
    model = PeftModel.from_pretrained(
        base_model_instance,
        adapter_path,
        torch_dtype=torch.float16,
    )
    
    logger.info("4. Merging adapter weights...")
    model = model.merge_and_unload()
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save merged model
    logger.info(f"5. Saving merged model to {output_path}...")
    model.save_pretrained(output_path, safe_serialization=True)
    tokenizer.save_pretrained(output_path)
    
    # Save merge info
    merge_info = {
        "base_model": base_model,
        "adapter_path": str(adapter_path),
        "merged": True,
        "torch_dtype": "float16",
    }
    with open(output_path / "merge_info.yaml", 'w') as f:
        yaml.dump(merge_info, f)
    
    logger.info("=" * 60)
    logger.info("Merge complete!")
    logger.info(f"Merged model saved to: {output_path}")
    logger.info("=" * 60)
    
    # Push to Hub if requested
    if push_to_hub and hub_model_id:
        logger.info(f"\n6. Pushing to HuggingFace Hub: {hub_model_id}")
        model.push_to_hub(hub_model_id)
        tokenizer.push_to_hub(hub_model_id)
        logger.info(f"Model pushed to: https://huggingface.co/{hub_model_id}")
    
    # Print next steps
    print("\nNext steps:")
    print(f"1. Test the merged model:")
    print(f"   python -c \"from transformers import pipeline; p = pipeline('text-generation', '{output_path}'); print(p('What is data privacy?'))\"")
    print(f"\n2. Convert to GGUF for Ollama:")
    print(f"   python convert_to_ollama.py --model {output_path} --name policy-compliance-llm")
    
    return model, tokenizer


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapter with base model")
    parser.add_argument("--adapter", type=str, required=True,
                        help="Path to the trained LoRA adapter directory")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to save the merged model")
    parser.add_argument("--base_model", type=str, default=None,
                        help="Base model ID (auto-detected if not provided)")
    parser.add_argument("--push_to_hub", action="store_true",
                        help="Push merged model to HuggingFace Hub")
    parser.add_argument("--hub_model_id", type=str, default=None,
                        help="HuggingFace Hub model ID (e.g., username/model-name)")
    
    args = parser.parse_args()
    
    merge_lora_adapter(
        adapter_path=args.adapter,
        output_path=args.output,
        base_model=args.base_model,
        push_to_hub=args.push_to_hub,
        hub_model_id=args.hub_model_id,
    )


if __name__ == "__main__":
    main()
