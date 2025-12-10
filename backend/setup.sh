#!/bin/bash
# Setup script for local backend server

echo "🔧 Setting up local backend environment..."

# Check Python version
python3 --version || { echo "❌ Python 3 not found"; exit 1; }

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Create .env file with your database connection:"
    echo "DATABASE_CONNECTION_TIMEWEB=postgresql://user:password@host:port/database"
fi

echo "✅ Setup complete!"
echo ""
echo "To start the backend server:"
echo "  source venv/bin/activate"
echo "  python3 run_local.py"
