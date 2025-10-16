#!/bin/bash

# SubtitlePlayer Launcher Script
# This script activates the virtual environment and runs the application

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check for virtual environment in parent directory first
PARENT_VENV="$(dirname $(dirname "$SCRIPT_DIR"))/.venv"
LOCAL_VENV="$SCRIPT_DIR/venv"

if [ -d "$PARENT_VENV" ]; then
    echo "Using virtual environment: $PARENT_VENV"
    source "$PARENT_VENV/bin/activate"
elif [ -d "$LOCAL_VENV" ]; then
    echo "Using virtual environment: $LOCAL_VENV"
    source "$LOCAL_VENV/bin/activate"
else
    echo "Virtual environment not found. Creating it..."
    python3 -m venv venv
    
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Run the application
python3 main.py

# Deactivate virtual environment on exit
deactivate
