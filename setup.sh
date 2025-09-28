#!/bin/bash

echo "🎬 Kling Video Generator - Setup Script"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "📍 Working directory: $SCRIPT_DIR"
echo ""

# Check Python version
echo "🔍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi
echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet
echo "✅ Pip upgraded"
echo ""

# Install Python dependencies
echo "📚 Installing Python dependencies..."
echo "   - Playwright (browser automation)"
echo "   - PyQt6 (GUI framework)"
pip install playwright PyQt6 --quiet
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi
echo "✅ Python dependencies installed"
echo ""

# Install Playwright browsers
echo "🌐 Installing Playwright Chromium browser..."
echo "   (This may take a few minutes...)"
playwright install chromium
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Chromium browser"
    exit 1
fi
echo "✅ Chromium browser installed"
echo ""

# Make start script executable
if [ -f "start.sh" ]; then
    chmod +x start.sh
    echo "✅ Start script is executable"
    echo ""
fi

# Verify installation
echo "🔬 Verifying installation..."
python -c "from playwright.sync_api import sync_playwright; print('  ✓ Playwright OK')" 2>&1
python -c "from PyQt6.QtWidgets import QApplication; print('  ✓ PyQt6 OK')" 2>&1
echo ""

# Summary
echo "========================================"
echo "🎉 Setup completed successfully!"
echo "========================================"
echo ""
echo "📖 Next steps:"
echo "   1. Run the application:"
echo "      ./start.sh"
echo ""
echo "   2. Or manually:"
echo "      source venv/bin/activate"
echo "      python gui_app.py"
echo ""
echo "💡 Tips:"
echo "   - On first run, you'll need to login to Kling"
echo "   - Session will be saved automatically"
echo "   - Use headless mode only after successful login"
echo ""
echo "📚 Documentation: see README.md"
echo ""