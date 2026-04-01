# refresh.ps1 - Kill Python, clear cache, and restart server
# Usage: .\refresh.ps1

Write-Host "`n=== REFRESH SCRIPT ===" -ForegroundColor Cyan
Write-Host "Killing Python processes..." -ForegroundColor Yellow

Get-Process python* -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Milliseconds 500

$pythonCheck = Get-Process python* -ErrorAction SilentlyContinue
if ($pythonCheck) {
    Write-Host "WARNING: Python processes still running!" -ForegroundColor Red
}
else {
    Write-Host "[OK] All Python processes terminated" -ForegroundColor Green
}

Write-Host "`nClearing Python cache..." -ForegroundColor Yellow

Remove-Item -Path __pycache__ -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path Scripts/__pycache__ -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "[OK] Cache cleared" -ForegroundColor Green

Write-Host "`nStarting server on port 8000..." -ForegroundColor Yellow
Write-Host "Server starting (press Ctrl+C to stop)" -ForegroundColor Cyan
Write-Host ""

Set-Location Scripts
python server.py 8000
