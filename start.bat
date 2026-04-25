@echo off
echo Starting Avanon PBM backend...
start "Backend" powershell -NoProfile -Command "cd '%~dp0backend'; python -m uvicorn main:app --port 8000 --reload"

echo Starting Avanon PBM frontend (production)...
start "Frontend" powershell -NoProfile -Command "cd '%~dp0frontend'; npx next start -p 3000"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Close the two terminal windows to stop the servers.
