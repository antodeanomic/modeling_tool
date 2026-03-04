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

REM Commented out: Closing extra PowerShell and Command windows interferes with execution
REM echo.
REM echo Closing extra PowerShell and Command windows...
REM taskkill /IM powershell.exe /F 2>nul >nul
REM taskkill /IM cmd.exe /F 2>nul >nul
REM timeout /t 1 /nobreak >nul
REM echo [OK] Extra console windows closed

echo.
echo Clearing Python cache...
rmdir /s /q __pycache__ 2>nul
rmdir /s /q Scripts\__pycache__ 2>nul
echo [OK] Cache cleared

echo.
echo Starting server on port 8000...
echo.

REM Use PowerShell to launch server in true background process
powershell -Command "Start-Process python -ArgumentList 'Scripts\server.py', '8000' -WindowStyle Hidden; Start-Sleep -Seconds 3"

REM Verify server is running
tasklist /FI "IMAGENAME eq python*" /FO TABLE 2>nul | findstr python >nul
if %errorlevel% equ 0 (
  echo [OK] Server started successfully and is running
  echo Server running at http://localhost:8000
) else (
  echo [ERROR] Server failed to start
)
echo.
