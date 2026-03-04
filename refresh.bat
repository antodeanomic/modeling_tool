@echo off
REM refresh.bat - Simple server restart script
REM Only manages Python server process - leaves all terminals alone

echo.
echo === SEQUENCE DIAGRAM SERVER RESTART ===
echo.

echo Step 1: Stopping any existing Python server processes...
taskkill /IM python3.13.exe /F 2>nul >nul
taskkill /IM python.exe /F 2>nul >nul
timeout /t 1 /nobreak >nul
echo [OK] Python processes stopped
echo.

echo Step 2: Clearing Python cache...
rmdir /s /q __pycache__ 2>nul
rmdir /s /q Scripts\__pycache__ 2>nul
timeout /t 1 /nobreak >nul
echo [OK] Cache cleared
echo.

echo Step 3: Starting server on port 8000...
echo Server will open in a NEW VISIBLE WINDOW below
echo.
echo ============================================
echo.

REM Start server in a NEW VISIBLE window so you can see output and errors
cd Scripts
start "Sequence Diagram Server" python server.py 8000
cd ..

REM Wait for server to fully start
timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo.
echo [OK] Server started!
echo.
echo Open in browser: http://localhost:8000
echo.
echo To stop the server: Close the Sequence Diagram Server window
echo.

