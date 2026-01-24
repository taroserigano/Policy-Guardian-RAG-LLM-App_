"""
Convert Fine-Tuned Model to Ollama Format

This script converts a HuggingFace model to GGUF format and creates
an Ollama model that can be run locally.

Usage:
    python convert_to_ollama.py --model ../outputs/merged/policy-llama --name policy-compliance-llm
    python convert_to_ollama.py --model ../outputs/merged/policy-llama --name policy-compliance-llm --quantization Q4_K_M
"""

import os
import sys
import argparse
import subprocess
import logging
import tempfile
from pathlib import Path
import shutil

import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Ollama Modelfile template for Llama 3.1
MODELFILE_TEMPLATE = '''FROM {gguf_path}

# Model parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 50
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096

# System prompt for policy compliance
SYSTEM """You are a compliance assistant specializing in corporate policies. You provide accurate, helpful answers about policy requirements, procedures, and best practices. When answering questions:

1. Be precise and cite specific policy sections when relevant
2. Explain compliance requirements clearly
3. Provide practical guidance for implementation
4. Flag potential compliance risks
5. If unsure, recommend consulting the full policy document

Always prioritize accuracy over brevity when discussing policy matters."""

# License and metadata
LICENSE """This model is fine-tuned for policy compliance assistance. Use responsibly and verify important compliance decisions with qualified professionals."""
'''


def check_dependencies():
    """Check if required tools are available."""
    # Check for llama.cpp (for GGUF conversion)
    llama_cpp_path = shutil.which("llama-quantize") or shutil.which("quantize")
    
    # Check for Ollama
    ollama_path = shutil.which("ollama")
    
    return {
        "llama_cpp": llama_cpp_path,
        "ollama": ollama_path,
    }


def convert_to_gguf(
    model_path: str,
    output_path: str,
    quantization: str = "Q4_K_M",
) -> str:
    """
    Convert HuggingFace model to GGUF format.
    
    This requires llama.cpp to be installed.
    Alternative: Use HuggingFace's convert script.
    """
    model_path = Path(model_path)
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Output GGUF filename
    gguf_filename = f"policy-llm-{quantization.lower()}.gguf"
    gguf_path = output_path / gguf_filename
    
    logger.info(f"Converting model to GGUF format: {quantization}")
    logger.info(f"Input: {model_path}")
    logger.info(f"Output: {gguf_path}")
    
    # Method 1: Try using llama-cpp-python's convert script
    try:
        # First convert to FP16 GGUF
        fp16_path = output_path / "model-fp16.gguf"
        
        # Use the convert script from llama-cpp-python or llama.cpp
        convert_script = None
        
        # Try to find the convert script
        possible_paths = [
            Path(sys.prefix) / "lib" / "python3.12" / "site-packages" / "llama_cpp" / "convert.py",
            Path.home() / "llama.cpp" / "convert.py",
            Path.home() / "llama.cpp" / "convert-hf-to-gguf.py",
        ]
        
        for p in possible_paths:
            if p.exists():
                convert_script = p
                break
        
        if convert_script:
            logger.info(f"Using convert script: {convert_script}")
            subprocess.run([
                sys.executable, str(convert_script),
                str(model_path),
                "--outfile", str(fp16_path),
                "--outtype", "f16",
            ], check=True)
            
            # Then quantize if needed
            if quantization.upper() != "F16":
                quantize_cmd = shutil.which("llama-quantize") or shutil.which("quantize")
                if quantize_cmd:
                    subprocess.run([
                        quantize_cmd,
                        str(fp16_path),
                        str(gguf_path),
                        quantization.upper(),
                    ], check=True)
                    # Remove FP16 intermediate
                    fp16_path.unlink()
                else:
                    logger.warning("Quantize tool not found. Using FP16 output.")
                    gguf_path = fp16_path
            else:
                gguf_path = fp16_path
                
            return str(gguf_path)
        
    except Exception as e:
        logger.warning(f"llama.cpp conversion failed: {e}")
    
    # Method 2: Try using transformers + ctransformers
    try:
        logger.info("Trying alternative conversion method...")
        
        # This is a placeholder - in practice you'd use:
        # - llama.cpp's convert-hf-to-gguf.py script
        # - or the gguf Python library
        
        raise NotImplementedError("Please install llama.cpp for GGUF conversion")
        
    except Exception as e:
        logger.error(f"All conversion methods failed: {e}")
        raise
    
    return str(gguf_path)


def create_ollama_model(
    gguf_path: str,
    model_name: str,
    system_prompt: str = None,
) -> bool:
    """
    Create an Ollama model from a GGUF file.
    """
    gguf_path = Path(gguf_path)
    
    if not gguf_path.exists():
        raise FileNotFoundError(f"GGUF file not found: {gguf_path}")
    
    logger.info(f"Creating Ollama model: {model_name}")
    
    # Create Modelfile
    modelfile_content = MODELFILE_TEMPLATE.format(gguf_path=str(gguf_path.absolute()))
    
    # Write Modelfile
    modelfile_path = gguf_path.parent / "Modelfile"
    with open(modelfile_path, 'w') as f:
        f.write(modelfile_content)
    
    logger.info(f"Created Modelfile at: {modelfile_path}")
    
    # Create Ollama model
    try:
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", str(modelfile_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Ollama model created successfully: {model_name}")
        logger.info(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create Ollama model: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("Ollama not found. Please install Ollama: https://ollama.ai")
        return False


def create_modelfile_only(
    gguf_path: str,
    output_dir: str,
    model_name: str,
) -> str:
    """
    Create just the Modelfile without running ollama create.
    Useful when Ollama is not installed or for manual creation.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    modelfile_content = MODELFILE_TEMPLATE.format(gguf_path=gguf_path)
    
    modelfile_path = output_dir / "Modelfile"
    with open(modelfile_path, 'w') as f:
        f.write(modelfile_content)
    
    # Also create a README
    readme_content = f"""# {model_name}

Policy Compliance Fine-Tuned LLM for Ollama

## Installation

1. Make sure Ollama is installed: https://ollama.ai

2. Create the model:
```bash
cd {output_dir}
ollama create {model_name} -f Modelfile
```

3. Run the model:
```bash
ollama run {model_name}
```

## Usage

```bash
# Interactive chat
ollama run {model_name}

# Single query
ollama run {model_name} "What are the key requirements for data privacy compliance?"

# API usage
curl http://localhost:11434/api/generate -d '{{
  "model": "{model_name}",
  "prompt": "What are the key requirements for data privacy compliance?"
}}'
```

## Model Info

- Base: Llama 3.1 8B
- Fine-tuning: QLoRA on policy compliance data
- Quantization: Q4_K_M
"""
    
    readme_path = output_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    logger.info(f"Created Modelfile at: {modelfile_path}")
    logger.info(f"Created README at: {readme_path}")
    
    return str(modelfile_path)


def main():
    parser = argparse.ArgumentParser(description="Convert fine-tuned model to Ollama format")
    parser.add_argument("--model", type=str, required=True,
                        help="Path to the merged HuggingFace model")
    parser.add_argument("--name", type=str, required=True,
                        help="Name for the Ollama model")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory for GGUF files (default: ../outputs/gguf)")
    parser.add_argument("--quantization", type=str, default="Q4_K_M",
                        choices=["Q4_K_M", "Q5_K_M", "Q8_0", "F16"],
                        help="Quantization type for GGUF")
    parser.add_argument("--skip_convert", action="store_true",
                        help="Skip GGUF conversion (use existing GGUF file)")
    parser.add_argument("--gguf_path", type=str, default=None,
                        help="Path to existing GGUF file (use with --skip_convert)")
    parser.add_argument("--modelfile_only", action="store_true",
                        help="Only create Modelfile without running ollama create")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Converting Fine-Tuned Model to Ollama Format")
    logger.info("=" * 60)
    
    # Check dependencies
    deps = check_dependencies()
    logger.info(f"Dependencies: {deps}")
    
    # Set output directory
    script_dir = Path(__file__).parent
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = (script_dir / ".." / "outputs" / "gguf").resolve()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to GGUF if needed
    if args.skip_convert:
        if not args.gguf_path:
            logger.error("--gguf_path required when using --skip_convert")
            sys.exit(1)
        gguf_path = args.gguf_path
    else:
        if not deps["llama_cpp"]:
            logger.warning("llama.cpp not found. Creating Modelfile only.")
            logger.info("To complete conversion, install llama.cpp:")
            logger.info("  git clone https://github.com/ggerganov/llama.cpp")
            logger.info("  cd llama.cpp && make")
            
            # Create a placeholder Modelfile
            modelfile_path = create_modelfile_only(
                gguf_path="<PATH_TO_GGUF_FILE>",
                output_dir=str(output_dir),
                model_name=args.name,
            )
            
            print("\n" + "=" * 60)
            print("Manual Steps Required:")
            print("=" * 60)
            print(f"\n1. Install llama.cpp and convert model to GGUF:")
            print(f"   python convert-hf-to-gguf.py {args.model} --outfile {output_dir}/model.gguf")
            print(f"\n2. Update the Modelfile with the GGUF path:")
            print(f"   Edit: {modelfile_path}")
            print(f"\n3. Create Ollama model:")
            print(f"   ollama create {args.name} -f {modelfile_path}")
            
            return
        
        try:
            gguf_path = convert_to_gguf(
                model_path=args.model,
                output_path=str(output_dir),
                quantization=args.quantization,
            )
        except Exception as e:
            logger.error(f"GGUF conversion failed: {e}")
            
            # Create Modelfile anyway for manual completion
            create_modelfile_only(
                gguf_path="<PATH_TO_GGUF_FILE>",
                output_dir=str(output_dir),
                model_name=args.name,
            )
            sys.exit(1)
    
    # Create Ollama model
    if args.modelfile_only:
        create_modelfile_only(
            gguf_path=gguf_path,
            output_dir=str(output_dir),
            model_name=args.name,
        )
    else:
        if not deps["ollama"]:
            logger.warning("Ollama not found. Creating Modelfile only.")
            create_modelfile_only(
                gguf_path=gguf_path,
                output_dir=str(output_dir),
                model_name=args.name,
            )
            print(f"\nTo create the Ollama model manually:")
            print(f"  ollama create {args.name} -f {output_dir}/Modelfile")
        else:
            success = create_ollama_model(
                gguf_path=gguf_path,
                model_name=args.name,
            )
            
            if success:
                print("\n" + "=" * 60)
                print("Conversion Complete!")
                print("=" * 60)
                print(f"\nYour model is ready! Run it with:")
                print(f"  ollama run {args.name}")
                print(f"\nOr use it in your application:")
                print(f'  OLLAMA_MODEL="{args.name}"')


if __name__ == "__main__":
    main()
