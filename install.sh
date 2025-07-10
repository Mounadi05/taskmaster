#!/bin/bash

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt 
else
    echo "No requirements.txt found"
fi

echo "Setup complete!"