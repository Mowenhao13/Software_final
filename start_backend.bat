@echo off
chcp 65001 >nul
cd /d "%~dp0backend"

echo ========================================
echo   Supply Chain Analytics - Backend
echo ========================================
echo.
echo Installing dependencies...
pip install -r requirements.txt -q
echo.
echo Initializing database...
python seed_data.py
echo.
echo Starting backend server at http://localhost:8000
echo API docs: http://localhost:8000/api/docs
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
