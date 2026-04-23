@echo off
echo Starting Auto Data Visualization App...
echo.

echo [1/2] Installing backend dependencies...
cd backend
pip install -r requirements.txt
echo.

echo [2/2] Starting FastAPI backend on port 8000...
start "FastAPI Backend" cmd /k "uvicorn main:app --reload --port 8000"

cd ../frontend

echo Installing frontend dependencies...
call npm install

echo Starting React frontend on port 5173...
start "React Frontend" cmd /k "npm run dev"

echo.
echo ✅ Both servers starting!
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:5173
echo.
pause
