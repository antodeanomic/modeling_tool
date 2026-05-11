# refresh.ps1 - Kill Python and clear cache (no server start)
# Usage: .\refresh.ps1

Write-Host "`n=== ENVIRONMENT REFRESH SCRIPT ===" -ForegroundColor Cyan
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

Write-Host "`nRefresh complete" -ForegroundColor Cyan
Write-Host "[OK] No server was started" -ForegroundColor Green
Write-Host "[OK] No browser was opened" -ForegroundColor Green
Write-Host ""
Write-Host "Next step (manual):" -ForegroundColor Yellow
Write-Host "  .\.venv\Scripts\python.exe Scripts\server.py 8000"
Write-Host "  Open VS Code browser at: http://localhost:8000"
