#!/bin/bash

# Installation Script for SubtitlePlayer
# This script automates the installation process on Linux

echo "=========================================="
echo "  SubtitlePlayer Installation Script"
echo "=========================================="
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Error: This script is for Linux systems only."
    exit 1
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3 using your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check for VLC
if ! command -v vlc &> /dev/null; then
    echo "⚠️  Warning: VLC is not installed."
    echo "VLC is required for video playback."
    echo ""
    read -p "Would you like to install VLC now? (y/n): " install_vlc
    
    if [[ $install_vlc == "y" || $install_vlc == "Y" ]]; then
        # Detect package manager
        if command -v apt &> /dev/null; then
            echo "Installing VLC using apt..."
            sudo apt update
            sudo apt install -y vlc libvlc-dev
        elif command -v dnf &> /dev/null; then
            echo "Installing VLC using dnf..."
            sudo dnf install -y vlc vlc-devel
        elif command -v pacman &> /dev/null; then
            echo "Installing VLC using pacman..."
            sudo pacman -S --noconfirm vlc
        else
            echo "❌ Could not detect package manager. Please install VLC manually."
            exit 1
        fi
    else
        echo "⚠️  Please install VLC manually before running SubtitlePlayer."
        exit 1
    fi
fi

echo "✓ VLC found"

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "  ✓ Installation Complete!"
    echo "=========================================="
    echo ""
    echo "To run SubtitlePlayer:"
    echo "  1. Make the launcher executable: chmod +x run.sh"
    echo "  2. Run: ./run.sh"
    echo ""
    echo "Or manually:"
    echo "  1. Activate virtual environment: source venv/bin/activate"
    echo "  2. Run: python3 main.py"
    echo ""
    echo "Don't forget to get your free API key from:"
    echo "  https://www.opensubtitles.com/api"
    echo ""
    
    # Make run.sh executable
    chmod +x run.sh
    
    read -p "Would you like to run SubtitlePlayer now? (y/n): " run_now
    if [[ $run_now == "y" || $run_now == "Y" ]]; then
        python3 main.py
    fi
else
    echo ""
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi

deactivate
