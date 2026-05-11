@echo off
REM refresh.bat - Environment cleanup/reset script
REM Does NOT start server or open browser

setlocal enabledelayedexpansion

echo.
echo === SEQUENCE DIAGRAM ENVIRONMENT REFRESH ===
echo.

echo Step 1: Stopping any existing Python server processes...
taskkill /IM python3.13.exe /F 2>&1 | findstr /v "not found" >nul
taskkill /IM python.exe /F 2>&1 | findstr /v "not found" >nul
timeout /t 1 /nobreak >nul
echo [OK] Python processes stopped
echo.

echo Step 2: Clearing Python cache...
if exist __pycache__ rmdir /s /q __pycache__ 2>nul
if exist Scripts\__pycache__ rmdir /s /q Scripts\__pycache__ 2>nul
timeout /t 1 /nobreak >nul
echo [OK] Cache cleared
echo.
echo Step 3: Refresh complete
echo [OK] No server was started
echo [OK] No browser was opened
echo.
echo Next step (manual):
echo   - Start server when needed: python Scripts\server.py 8000
echo   - Open VS Code browser to: http://localhost:8000
echo.



