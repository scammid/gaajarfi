@echo off
echo.
echo  ==========================================
echo      Gaajarfi - Carrot Champion App
echo  ==========================================
echo.

cd /d "%~dp0"

if not exist ".env" (
    echo  ERROR: .env file not found!
    echo  Copy .env.example to .env and add your REPLICATE_API_TOKEN.
    echo.
    pause
    exit /b
)

if not exist "venv" (
    echo  Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo  Installing dependencies...
pip install -r requirements.txt -q

echo.
echo  Starting Gaajarfi at http://localhost:5000
echo  Press Ctrl+C to stop.
echo.
set FLASK_ENV=development
python app.py
pause
