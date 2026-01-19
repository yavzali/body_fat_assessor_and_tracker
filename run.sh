#!/bin/bash

# Body Fat Tracker Startup Script

echo "🚀 Body Fat Tracker Startup"
echo "============================="
echo ""

# Check if virtual environment exists
if [ ! -d "backend/.venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run setup first:"
    echo "  cd backend"
    echo "  python -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Copying from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env and add your API keys before running again!"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source backend/.venv/bin/activate

# Check if database exists, if not initialize it
if [ ! -f "bodyfat_tracker.db" ]; then
    echo "📊 Initializing database..."
    cd backend
    python -c "from database import init_db; init_db()"
    cd ..
    echo "✅ Database initialized"
fi

# Build frontend widgets
echo "🔨 Building frontend widgets..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi
npm run build
cd ..
echo "✅ Widgets built"

# Start the server
echo ""
echo "🎉 Starting server on http://localhost:8000"
echo "============================="
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python main.py
