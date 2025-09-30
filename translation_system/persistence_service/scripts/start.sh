#!/bin/bash
# ============================================================================
# Persistence Service - Start Script
# ============================================================================

echo "Starting Persistence Service..."

# Change to project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if [ ! -f "venv/bin/uvicorn" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Create logs directory if not exists
mkdir -p logs

# Check if config.yaml exists
if [ ! -f "config/config.yaml" ]; then
    echo "Config file not found. Copying from example..."
    cp config/config.yaml.example config/config.yaml
    echo "Please edit config/config.yaml with your database settings"
    exit 1
fi

# Start the service
echo "Starting Uvicorn server..."
python main.py