# Refresh Workflow Analysis (Current)

## Summary
The refresh workflow is intentionally split into two steps:

1. `refresh.bat` / `refresh.ps1`: cleanup only
2. Manual server start: explicit and user-controlled

This avoids automatic browser launches that interfere with VS Code browser verification.

## Current Behavior

### refresh.bat and refresh.ps1
- Stop Python server processes
- Clear Python cache folders
- Do not start the server
- Do not open any browser

### Server Start (manual)
Use one of:
- `.venv\Scripts\python.exe Scripts\server.py 8000`
- `start_server.bat`
- VS Code task: `Start Server (Manual)`
- VS Code task: `Ensure Server Ready (Start If Needed)`

Then open VS Code browser to:
- `http://localhost:8000`

## Why This Is Cleaner
- No hidden side effects
- No external browser popups
- Reproducible verification path for agent and user
- Easier debugging of startup vs rendering issues

## Recommended Daily Flow
1. Run `refresh.bat`
2. Run `Ensure Server Ready (Start If Needed)`
3. Open VS Code browser at `http://localhost:8000`
4. Make code changes and refresh the page

## Notes
- CSV files still hot-reload on each request.
- Full tests should be run before commit milestones.
