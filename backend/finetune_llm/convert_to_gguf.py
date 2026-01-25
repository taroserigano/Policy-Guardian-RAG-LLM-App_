"""
Convert merged Llama model to GGUF Q4_K_M for Ollama
Requires: llama.cpp cloned in parent directory
"""

import os
import subprocess
import sys

print("=" * 60)
print("Converting to GGUF for Ollama")
print("=" * 60)

MERGED_MODEL = "./policy-llama-merged"
LLAMA_CPP = "../llama.cpp"
OUTPUT_FP16 = "./policy-compliance-llm-f16.gguf"
OUTPUT_Q4 = "./policy-compliance-llm-Q4_K_M.gguf"

# Check merged model exists
if not os.path.exists(MERGED_MODEL):
    print(f"❌ Error: Merged model not found at {MERGED_MODEL}")
    print("Run merge_adapter.py first")
    exit(1)

# Check/clone llama.cpp
if not os.path.exists(LLAMA_CPP):
    print(f"\n[1/5] Cloning llama.cpp...")
    subprocess.run([
        "git", "clone", 
        "https://github.com/ggerganov/llama.cpp.git",
        LLAMA_CPP
    ], check=True)
    print("✅ llama.cpp cloned")
else:
    print(f"\n[1/5] llama.cpp found at {LLAMA_CPP}")

# Install requirements
print(f"\n[2/5] Installing llama.cpp requirements...")
subprocess.run([
    sys.executable, "-m", "pip", "install", "-q",
    "-r", f"{LLAMA_CPP}/requirements.txt"
], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gguf"], check=True)
print("✅ Requirements installed")

# Convert to FP16 GGUF
print(f"\n[3/5] Converting to FP16 GGUF...")
print("      (This takes 5-10 minutes)")
subprocess.run([
    sys.executable,
    f"{LLAMA_CPP}/convert_hf_to_gguf.py",
    MERGED_MODEL,
    "--outtype", "f16",
    "--outfile", OUTPUT_FP16
], check=True)
print(f"✅ FP16 GGUF created: {OUTPUT_FP16}")

# Build llama.cpp quantize tool (Windows)
print(f"\n[4/5] Building llama.cpp quantize tool...")
quantize_exe = f"{LLAMA_CPP}/llama-quantize.exe"
if not os.path.exists(quantize_exe):
    print("      Building with CMake (takes 2-3 minutes)...")
    build_dir = f"{LLAMA_CPP}/build"
    os.makedirs(build_dir, exist_ok=True)
    
    # CMake configure
    subprocess.run([
        "cmake", "-S", LLAMA_CPP, "-B", build_dir,
        "-DCMAKE_BUILD_TYPE=Release"
    ], check=True)
    
    # CMake build
    subprocess.run([
        "cmake", "--build", build_dir, "--config", "Release"
    ], check=True)
    
    # Copy executable
    subprocess.run([
        "copy", f"{build_dir}\\bin\\Release\\llama-quantize.exe", quantize_exe
    ], shell=True, check=True)
    
print(f"✅ Quantize tool ready")

# Quantize to Q4_K_M
print(f"\n[5/5] Quantizing to Q4_K_M...")
print("      (This takes 3-5 minutes, reduces size from ~16GB to ~5GB)")
subprocess.run([
    quantize_exe,
    OUTPUT_FP16,
    OUTPUT_Q4,
    "Q4_K_M"
], check=True)

# Get file size
size_gb = os.path.getsize(OUTPUT_Q4) / (1024**3)

print("\n" + "=" * 60)
print("✅ SUCCESS! GGUF model created:")
print(f"   {os.path.abspath(OUTPUT_Q4)}")
print(f"   Size: {size_gb:.2f} GB")
print("=" * 60)
print("\nNext step: Create Modelfile and import to Ollama")
print("Run: python import_to_ollama.py")
