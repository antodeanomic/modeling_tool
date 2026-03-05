@echo off
REM refresh.bat - Simple server restart script
REM Uses PowerShell for reliable process launching

setlocal enabledelayedexpansion

echo.
echo === SEQUENCE DIAGRAM SERVER RESTART ===
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

echo Step 3: Starting server on port 8000...
echo Server will open in a NEW VISIBLE WINDOW
echo.

REM Use PowerShell to launch the server
set SCRIPTDIR=%CD%\Scripts
set LOGPATH=%CD%\server_output.log

REM Launch server with PowerShell (output to log, errors to separate file)
powershell -NoProfile -Command "Start-Process -FilePath python -ArgumentList 'server.py', '8000' -WorkingDirectory '%SCRIPTDIR%' -PassThru -WindowStyle Normal -RedirectStandardOutput '%LOGPATH%' | ForEach-Object {Write-Host '[OK] Server started (PID:' $_.Id ')'}"

timeout /t 3 /nobreak >nul

echo.
echo Step 4: Opening browser at http://localhost:8000
powershell -NoProfile -Command "Start-Sleep -Milliseconds 500; Start-Process 'http://localhost:8000'" 2>nul
echo [OK] Browser opening requested
echo.
echo To stop the server: Close the server window
echo Server output logged to: %LOGPATH%
echo.



