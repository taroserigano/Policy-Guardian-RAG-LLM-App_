@echo off
echo ================================================================================
echo FINE-TUNED MODEL COMPARISON TEST
echo ================================================================================
echo.
echo This will compare your fine-tuned policy-compliance-llm against base llama3.1:8b
echo Expected runtime: ~2-3 minutes for 3 test questions
echo.
pause

cd /d "%~dp0"

echo.
echo Running comparison test...
echo.

python auto_compare.py

echo.
echo ================================================================================
echo.
echo Results saved to: comparison_results.json
echo.
if exist comparison_results.json (
    echo Opening results...
    type comparison_results.json
)

echo.
echo.
pause
