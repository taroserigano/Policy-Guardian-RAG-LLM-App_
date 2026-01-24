"""
QLoRA Fine-Tuning Script for Policy Compliance LLM

This script fine-tunes a base LLM using QLoRA (4-bit quantization + LoRA)
on policy compliance training data.

Usage:
    python finetune_qlora.py --config ../config/qlora_config.yaml
    python finetune_qlora.py --base_model meta-llama/Meta-Llama-3.1-8B-Instruct --data ../data/processed/training_data.jsonl
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import torch
import yaml
from datasets import Dataset, load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    DataCollatorForLanguageModeling,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType,
)
from trl import SFTTrainer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_quantization_config(config: Dict) -> BitsAndBytesConfig:
    """Create BitsAndBytes quantization configuration for 4-bit QLoRA."""
    quant_config = config.get('quantization', {})
    
    compute_dtype = getattr(torch, quant_config.get('bnb_4bit_compute_dtype', 'float16'))
    
    return BitsAndBytesConfig(
        load_in_4bit=quant_config.get('load_in_4bit', True),
        bnb_4bit_quant_type=quant_config.get('bnb_4bit_quant_type', 'nf4'),
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=quant_config.get('bnb_4bit_use_double_quant', True),
    )


def setup_lora_config(config: Dict) -> LoraConfig:
    """Create LoRA configuration."""
    lora_config = config.get('lora', {})
    
    return LoraConfig(
        r=lora_config.get('r', 64),
        lora_alpha=lora_config.get('lora_alpha', 128),
        lora_dropout=lora_config.get('lora_dropout', 0.05),
        bias=lora_config.get('bias', 'none'),
        task_type=TaskType.CAUSAL_LM,
        target_modules=lora_config.get('target_modules', [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ]),
    )


def load_model_and_tokenizer(config: Dict, bnb_config: BitsAndBytesConfig):
    """Load the base model with 4-bit quantization and tokenizer."""
    model_config = config.get('model', {})
    base_model = model_config.get('base_model', 'meta-llama/Meta-Llama-3.1-8B-Instruct')
    
    logger.info(f"Loading base model: {base_model}")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        base_model,
        trust_remote_code=True,
    )
    
    # Set padding token if not set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    
    # Load model with quantization
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map=model_config.get('device_map', 'auto'),
        trust_remote_code=True,
        torch_dtype=getattr(torch, model_config.get('torch_dtype', 'float16')),
    )
    
    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)
    
    # Enable gradient checkpointing for memory efficiency
    model.gradient_checkpointing_enable()
    
    logger.info(f"Model loaded successfully. Parameters: {model.num_parameters():,}")
    
    return model, tokenizer


def load_training_data(config: Dict, tokenizer) -> tuple:
    """Load and prepare training dataset."""
    dataset_config = config.get('dataset', {})
    data_file = dataset_config.get('train_file', './data/processed/training_data.jsonl')
    
    logger.info(f"Loading training data from: {data_file}")
    
    # Load JSONL data
    data = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    logger.info(f"Loaded {len(data)} training examples")
    
    # Get prompt template
    prompt_template = dataset_config.get('prompt_template', """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a compliance assistant specializing in corporate policies. You provide accurate, helpful answers about policy requirements, procedures, and best practices. Always cite specific policy requirements when applicable.<|eot_id|><|start_header_id|>user<|end_header_id|>

{instruction}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{response}<|eot_id|>""")
    
    # Format data
    def format_example(example):
        # Handle different input formats
        if 'instruction' in example:
            instruction = example['instruction']
            if example.get('input'):
                instruction = f"{instruction}\n\n{example['input']}"
            response = example.get('output', example.get('response', ''))
        elif 'question' in example:
            instruction = example['question']
            response = example.get('answer', '')
        elif 'messages' in example:
            # Chat format
            messages = example['messages']
            instruction = next((m['content'] for m in messages if m['role'] == 'user'), '')
            response = next((m['content'] for m in messages if m['role'] == 'assistant'), '')
        else:
            instruction = str(example.get('prompt', ''))
            response = str(example.get('completion', ''))
        
        return {
            'text': prompt_template.format(instruction=instruction, response=response)
        }
    
    # Create dataset
    formatted_data = [format_example(d) for d in data]
    dataset = Dataset.from_list(formatted_data)
    
    # Split into train/eval
    eval_split = dataset_config.get('eval_split', 0.1)
    split_dataset = dataset.train_test_split(test_size=eval_split, seed=42)
    
    logger.info(f"Train examples: {len(split_dataset['train'])}")
    logger.info(f"Eval examples: {len(split_dataset['test'])}")
    
    return split_dataset['train'], split_dataset['test']


def setup_training_arguments(config: Dict) -> TrainingArguments:
    """Create training arguments from config."""
    train_config = config.get('training', {})
    
    return TrainingArguments(
        output_dir=train_config.get('output_dir', './outputs/adapters/policy-llama'),
        
        # Batch settings
        per_device_train_batch_size=train_config.get('per_device_train_batch_size', 4),
        per_device_eval_batch_size=train_config.get('per_device_eval_batch_size', 4),
        gradient_accumulation_steps=train_config.get('gradient_accumulation_steps', 4),
        
        # Training duration
        num_train_epochs=train_config.get('num_train_epochs', 3),
        max_steps=train_config.get('max_steps', -1),
        
        # Learning rate
        learning_rate=train_config.get('learning_rate', 2e-4),
        weight_decay=train_config.get('weight_decay', 0.01),
        warmup_ratio=train_config.get('warmup_ratio', 0.03),
        lr_scheduler_type=train_config.get('lr_scheduler_type', 'cosine'),
        
        # Optimization
        optim=train_config.get('optim', 'paged_adamw_32bit'),
        max_grad_norm=train_config.get('max_grad_norm', 0.3),
        
        # Logging
        logging_steps=train_config.get('logging_steps', 10),
        logging_dir=train_config.get('logging_dir', './outputs/logs'),
        report_to=train_config.get('report_to', 'none'),
        
        # Evaluation
        evaluation_strategy=train_config.get('evaluation_strategy', 'steps'),
        eval_steps=train_config.get('eval_steps', 50),
        
        # Checkpointing
        save_strategy=train_config.get('save_strategy', 'steps'),
        save_steps=train_config.get('save_steps', 100),
        save_total_limit=train_config.get('save_total_limit', 3),
        load_best_model_at_end=train_config.get('load_best_model_at_end', True),
        
        # Memory optimization
        fp16=train_config.get('fp16', True),
        bf16=train_config.get('bf16', False),
        gradient_checkpointing=train_config.get('gradient_checkpointing', True),
        
        # Reproducibility
        seed=train_config.get('seed', 42),
        
        # Misc
        remove_unused_columns=False,
        dataloader_pin_memory=True,
    )


def print_trainable_parameters(model):
    """Print the number of trainable parameters."""
    trainable_params = 0
    all_params = 0
    for _, param in model.named_parameters():
        all_params += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    
    logger.info(
        f"Trainable params: {trainable_params:,} || "
        f"All params: {all_params:,} || "
        f"Trainable%: {100 * trainable_params / all_params:.2f}%"
    )


def train(config: Dict):
    """Main training function."""
    logger.info("=" * 60)
    logger.info("QLoRA Fine-Tuning for Policy Compliance LLM")
    logger.info("=" * 60)
    
    # Check CUDA availability
    if torch.cuda.is_available():
        logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
        logger.info(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        logger.warning("CUDA not available! Training will be very slow on CPU.")
    
    # Setup configurations
    logger.info("\n1. Setting up configurations...")
    bnb_config = setup_quantization_config(config)
    lora_config = setup_lora_config(config)
    
    # Load model and tokenizer
    logger.info("\n2. Loading model and tokenizer...")
    model, tokenizer = load_model_and_tokenizer(config, bnb_config)
    
    # Apply LoRA
    logger.info("\n3. Applying LoRA adapter...")
    model = get_peft_model(model, lora_config)
    print_trainable_parameters(model)
    
    # Load training data
    logger.info("\n4. Loading training data...")
    train_dataset, eval_dataset = load_training_data(config, tokenizer)
    
    # Setup training arguments
    logger.info("\n5. Setting up training arguments...")
    training_args = setup_training_arguments(config)
    
    # Create output directory
    os.makedirs(training_args.output_dir, exist_ok=True)
    
    # Initialize trainer
    logger.info("\n6. Initializing trainer...")
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        dataset_text_field="text",
        max_seq_length=config.get('dataset', {}).get('max_seq_length', 2048),
        packing=False,
    )
    
    # Start training
    logger.info("\n7. Starting training...")
    logger.info("=" * 60)
    
    trainer.train()
    
    # Save final model
    logger.info("\n8. Saving final model...")
    final_output_dir = os.path.join(training_args.output_dir, "final")
    trainer.save_model(final_output_dir)
    tokenizer.save_pretrained(final_output_dir)
    
    # Save training config
    config_output = os.path.join(final_output_dir, "training_config.yaml")
    with open(config_output, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info(f"Model saved to: {final_output_dir}")
    logger.info("=" * 60)
    
    # Print next steps
    print("\nNext steps:")
    print(f"1. Merge adapter with base model:")
    print(f"   python merge_adapter.py --adapter {final_output_dir} --output ../outputs/merged/policy-llama")
    print(f"\n2. Convert to Ollama format:")
    print(f"   python convert_to_ollama.py --model ../outputs/merged/policy-llama --name policy-compliance-llm")
    
    return trainer


def main():
    parser = argparse.ArgumentParser(description="QLoRA Fine-Tuning for Policy Compliance LLM")
    parser.add_argument("--config", type=str, default="../config/qlora_config.yaml",
                        help="Path to configuration YAML file")
    parser.add_argument("--base_model", type=str, default=None,
                        help="Override base model from config")
    parser.add_argument("--data", type=str, default=None,
                        help="Override training data path from config")
    parser.add_argument("--output_dir", type=str, default=None,
                        help="Override output directory from config")
    parser.add_argument("--epochs", type=int, default=None,
                        help="Override number of epochs")
    parser.add_argument("--batch_size", type=int, default=None,
                        help="Override batch size")
    parser.add_argument("--learning_rate", type=float, default=None,
                        help="Override learning rate")
    
    args = parser.parse_args()
    
    # Load config
    script_dir = Path(__file__).parent
    config_path = (script_dir / args.config).resolve()
    
    if config_path.exists():
        config = load_config(str(config_path))
        logger.info(f"Loaded config from: {config_path}")
    else:
        logger.warning(f"Config not found at {config_path}, using defaults")
        config = {}
    
    # Apply command line overrides
    if args.base_model:
        config.setdefault('model', {})['base_model'] = args.base_model
    if args.data:
        config.setdefault('dataset', {})['train_file'] = args.data
    if args.output_dir:
        config.setdefault('training', {})['output_dir'] = args.output_dir
    if args.epochs:
        config.setdefault('training', {})['num_train_epochs'] = args.epochs
    if args.batch_size:
        config.setdefault('training', {})['per_device_train_batch_size'] = args.batch_size
    if args.learning_rate:
        config.setdefault('training', {})['learning_rate'] = args.learning_rate
    
    # Run training
    train(config)


if __name__ == "__main__":
    main()
