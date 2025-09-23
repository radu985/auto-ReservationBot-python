#!/bin/bash
echo "Starting VFS Global Automation System..."
echo

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements if needed
echo "Checking requirements..."
pip install -r requirements.txt --quiet

# Run the application
echo "Starting VFS Global Automation..."
python -m app.main
