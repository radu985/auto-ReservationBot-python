@echo off
echo Starting VFS Global Automation System...
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install requirements if needed
echo Checking requirements...
pip install -r requirements.txt --quiet

REM Run the application
echo Starting VFS Global Automation...
python -m app.main

pause
