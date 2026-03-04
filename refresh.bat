@echo off
REM refresh.bat - Kill Python, clear cache, and restart server
REM Usage: refresh.bat

echo.
echo === REFRESH SCRIPT ===
echo Killing Python processes...
taskkill /IM python3.13.exe /F 2>nul >nul
taskkill /IM python.exe /F 2>nul >nul
timeout /t 1 /nobreak >nul
echo.
echo [OK] Python processes terminated

echo.
echo Clearing Python cache...
rmdir /s /q __pycache__ 2>nul
rmdir /s /q Scripts\__pycache__ 2>nul
echo [OK] Cache cleared

echo.
echo Starting server on port 8000...
echo Server starting (press Ctrl+C to stop)
echo.

cd Scripts
python server.py 8000
