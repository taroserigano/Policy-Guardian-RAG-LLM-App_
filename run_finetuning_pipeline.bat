@echo off
REM Run the complete embedding fine-tuning pipeline

echo =====================================
echo Policy RAG - Embedding Fine-Tuning
echo =====================================
echo.

cd backend

echo Step 1/4: Generating training data...
python scripts/generate_training_data.py
if errorlevel 1 (
    echo ERROR: Training data generation failed!
    pause
    exit /b 1
)
echo.

echo Step 2/4: Fine-tuning embeddings...
python scripts/finetune_embeddings.py
if errorlevel 1 (
    echo ERROR: Fine-tuning failed!
    pause
    exit /b 1
)
echo.

echo Step 3/4: Evaluating model...
python scripts/evaluate_embeddings.py
if errorlevel 1 (
    echo ERROR: Evaluation failed!
    pause
    exit /b 1
)
echo.

echo Step 4/4: Setting up deployment...
python scripts/convert_to_ollama.py
echo.

echo =====================================
echo Pipeline Complete!
echo =====================================
echo.
echo Next steps:
echo 1. Start embedding server:
echo    cd backend\models
echo    python embedding_server.py
echo.
echo 2. Test in frontend:
echo    - Embedding model dropdown should show "Policy (Fine-tuned)"
echo    - Select it for document uploads and queries
echo.

pause
