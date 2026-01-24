@echo off
REM QLoRA Fine-Tuning Pipeline for Policy Compliance LLM
REM ====================================================

echo ============================================================
echo QLoRA Fine-Tuning Pipeline
echo ============================================================

cd /d "%~dp0"

:menu
echo.
echo Select an option:
echo   1. Generate Training Data (requires Ollama running)
echo   2. Install Fine-tuning Dependencies
echo   3. Run QLoRA Fine-tuning (requires GPU + HuggingFace token)
echo   4. Merge LoRA Adapter
echo   5. Convert to Ollama Model
echo   6. Run Full Pipeline (1-5)
echo   7. Check Training Data Status
echo   8. Exit
echo.

set /p choice="Enter choice (1-8): "

if "%choice%"=="1" goto generate_data
if "%choice%"=="2" goto install_deps
if "%choice%"=="3" goto finetune
if "%choice%"=="4" goto merge
if "%choice%"=="5" goto convert
if "%choice%"=="6" goto full_pipeline
if "%choice%"=="7" goto check_status
if "%choice%"=="8" goto end
goto menu

:generate_data
echo.
echo [Step 1] Generating Training Data...
echo This will use Ollama to create Q&A pairs from policy documents.
echo Estimated time: 15-30 minutes
echo.
python scripts\generate_training_data.py
if errorlevel 1 (
    echo Error generating training data!
    pause
    goto menu
)
echo Training data generated successfully!
pause
goto menu

:install_deps
echo.
echo [Step 2] Installing Fine-tuning Dependencies...
echo This requires a Python environment with CUDA support.
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo Error installing dependencies!
    echo Make sure you have CUDA and PyTorch installed.
    pause
    goto menu
)
echo Dependencies installed successfully!
pause
goto menu

:finetune
echo.
echo [Step 3] Running QLoRA Fine-tuning...
echo This requires:
echo   - NVIDIA GPU with 8GB+ VRAM
echo   - HuggingFace token (for Llama 3.1 access)
echo   - Training data in data/processed/
echo.
set /p HF_TOKEN="Enter HuggingFace token (or press Enter to skip): "
if not "%HF_TOKEN%"=="" (
    set HUGGING_FACE_HUB_TOKEN=%HF_TOKEN%
)
python scripts\finetune_qlora.py --config config\qlora_config.yaml
if errorlevel 1 (
    echo Error during fine-tuning!
    pause
    goto menu
)
echo Fine-tuning complete!
pause
goto menu

:merge
echo.
echo [Step 4] Merging LoRA Adapter with Base Model...
echo.
python scripts\merge_adapter.py --adapter outputs\adapters\policy-llama\final --output outputs\merged\policy-llama
if errorlevel 1 (
    echo Error merging adapter!
    pause
    goto menu
)
echo Adapter merged successfully!
pause
goto menu

:convert
echo.
echo [Step 5] Converting to Ollama Model...
echo.
set /p MODEL_NAME="Enter Ollama model name (default: policy-compliance-llm): "
if "%MODEL_NAME%"=="" set MODEL_NAME=policy-compliance-llm
python scripts\convert_to_ollama.py --model outputs\merged\policy-llama --name %MODEL_NAME%
if errorlevel 1 (
    echo Error converting to Ollama!
    echo You may need to install llama.cpp manually.
    pause
    goto menu
)
echo Model converted to Ollama format!
echo Run with: ollama run %MODEL_NAME%
pause
goto menu

:full_pipeline
echo.
echo Running Full Pipeline...
echo ========================
call :generate_data_silent
call :install_deps_silent
call :finetune_silent
call :merge_silent
call :convert_silent
echo.
echo Full pipeline complete!
pause
goto menu

:generate_data_silent
echo [1/5] Generating training data...
python scripts\generate_training_data.py
exit /b

:install_deps_silent
echo [2/5] Installing dependencies...
pip install -r requirements.txt
exit /b

:finetune_silent
echo [3/5] Fine-tuning model...
python scripts\finetune_qlora.py --config config\qlora_config.yaml
exit /b

:merge_silent
echo [4/5] Merging adapter...
python scripts\merge_adapter.py --adapter outputs\adapters\policy-llama\final --output outputs\merged\policy-llama
exit /b

:convert_silent
echo [5/5] Converting to Ollama...
python scripts\convert_to_ollama.py --model outputs\merged\policy-llama --name policy-compliance-llm
exit /b

:check_status
echo.
echo Checking Training Data Status...
echo ================================
if exist "data\processed\training_data.jsonl" (
    echo Training data found!
    for %%A in ("data\processed\training_data.jsonl") do echo   Size: %%~zA bytes
    findstr /R /N "^" "data\processed\training_data.jsonl" | find /C ":" > temp_count.txt
    set /p LINE_COUNT=<temp_count.txt
    del temp_count.txt
    echo   Lines: Checking...
) else (
    echo No training data found. Run option 1 first.
)
echo.
if exist "data\processed\training_data.alpaca.jsonl" (
    echo Alpaca format data found!
)
if exist "data\processed\training_data.chat.jsonl" (
    echo Chat format data found!
)
echo.
if exist "outputs\adapters\policy-llama\final" (
    echo Fine-tuned adapter found!
) else (
    echo No fine-tuned adapter yet.
)
echo.
if exist "outputs\merged\policy-llama" (
    echo Merged model found!
) else (
    echo No merged model yet.
)
pause
goto menu

:end
echo Goodbye!
exit /b 0
