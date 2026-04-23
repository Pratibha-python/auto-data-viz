#!/bin/bash
echo "🚀 Starting Auto Data Visualization App..."

# Backend
echo "→ Setting up Python backend..."
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Frontend
echo "→ Setting up React frontend..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ App is running!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait and clean up
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Servers stopped.'" INT
wait
