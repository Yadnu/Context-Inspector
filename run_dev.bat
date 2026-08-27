@echo off
echo ===================================================
echo   Clause Lens — Starting Development Environment
echo ===================================================
echo.

echo [1/2] Starting FastMCP Python Server on http://localhost:8000...
start "Clause Lens FastMCP Server" cmd /k ".venv\Scripts\python.exe -m uvicorn server.main:app --host 0.0.0.0 --port 8000"

echo [2/2] Starting Next.js Web Client on http://localhost:3000...
start "Clause Lens Web Client" cmd /k "cd web && npm run dev"

echo.
echo Setup complete! Both processes launched in separate windows.
echo   - Web Client: http://localhost:3000
echo   - MCP Server: http://localhost:8000
echo.
pause
