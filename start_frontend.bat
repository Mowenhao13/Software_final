@echo off
chcp 65001 >nul
cd /d "%~dp0frontend"

echo ========================================
echo   Supply Chain Analytics - Frontend
echo ========================================
echo.
echo Installing dependencies...
call npm install
echo.
echo Starting frontend dev server at http://localhost:5173
echo.
call npm run dev
pause
