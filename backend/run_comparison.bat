@echo off
echo ================================================================================
echo Testing Fine-Tuned Model vs Base Model
echo ================================================================================
echo.
echo This will compare policy-compliance-llm against llama3.1:8b
echo.
echo Running quick comparison first...
echo.

cd /d "%~dp0"
python quick_compare.py

echo.
echo.
echo ================================================================================
echo Ready for full comparison?
echo The full test runs 10 questions and takes ~10 minutes
echo ================================================================================
echo.
set /p response="Run full comparison? (y/n): "

if /i "%response%"=="y" (
    echo.
    echo Running full comparison...
    python compare_models.py
) else (
    echo.
    echo Skipped full comparison. Run 'python compare_models.py' manually later.
)

echo.
echo Press any key to exit...
pause > nul
