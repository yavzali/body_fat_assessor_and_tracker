@echo off
REM Body Fat Tracker Startup Script for Windows

echo 🚀 Body Fat Tracker Startup
echo =============================
echo.

REM Check if virtual environment exists
if not exist "backend\.venv" (
    echo ❌ Virtual environment not found!
    echo Please run setup first:
    echo   cd backend
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found!
    echo Copying from .env.example...
    copy .env.example .env
    echo ✅ Created .env file
    echo ⚠️  Please edit .env and add your API keys before running again!
    exit /b 1
)

REM Activate virtual environment
echo 📦 Activating virtual environment...
call backend\.venv\Scripts\activate

REM Check if database exists, if not initialize it
if not exist "bodyfat_tracker.db" (
    echo 📊 Initializing database...
    cd backend
    python -c "from database import init_db; init_db()"
    cd ..
    echo ✅ Database initialized
)

REM Build frontend widgets
echo 🔨 Building frontend widgets...
cd frontend
if not exist "node_modules" (
    echo 📦 Installing frontend dependencies...
    call npm install
)
call npm run build
cd ..
echo ✅ Widgets built

REM Start the server
echo.
echo 🎉 Starting server on http://localhost:8000
echo =============================
echo.
echo Press Ctrl+C to stop the server
echo.

cd backend
python main.py
