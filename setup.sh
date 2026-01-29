#!/bin/bash

# LiveKit Voice Agent Setup Script

echo "============================================"
echo "LiveKit Voice Agent Setup"
echo "============================================"
echo ""

# Check Python version
echo "Checking Python version..."
python --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment (instructions only)
echo ""
echo "============================================"
echo "Virtual environment created!"
echo "To activate it, run:"
echo ""
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  .\\venv\\Scripts\\activate"
else
    echo "  source venv/bin/activate"
fi
echo "============================================"
echo ""
echo "After activation, run:"
echo "  pip install -r requirements.txt"
echo "  cp .env.example .env"
echo "  # Edit .env with your credentials"
echo "  python webhook_handler.py"
echo ""
