@echo off
REM start_server.bat - Manual server start helper (no browser launch)

setlocal

set PYTHON_EXE=%CD%\.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo.
echo === START SERVER (MANUAL) ===
echo Using Python: %PYTHON_EXE%
echo URL: http://localhost:8000
echo Press Ctrl+C to stop
echo.

"%PYTHON_EXE%" Scripts\server.py 8000
