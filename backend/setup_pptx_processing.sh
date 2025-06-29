#!/bin/bash

# Setup script for PPTX preprocessing functionality
# This script installs dependencies and tests the installation

set -e  # Exit on any error

echo "🚀 Setting up PPTX preprocessing for Gym Chatbot"
echo "================================================"

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: This script must be run from the backend directory"
    echo "Please run: cd backend && ./setup_pptx_processing.sh"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not detected"
    echo "It's recommended to activate your virtual environment first:"
    echo "  source venv/bin/activate  # or your venv path"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Installing dependencies..."

# Install requirements
pip install -r requirements.txt

echo "✅ Dependencies installed"

# Test the installation
echo ""
echo "🧪 Testing installation..."

# Test python-pptx import
if python -c "import pptx; print('✅ python-pptx imported successfully')" 2>/dev/null; then
    echo "✅ python-pptx library is working"
else
    echo "❌ python-pptx import failed"
    echo "Try installing manually: pip install python-pptx"
    exit 1
fi

# Test our preprocessing module
if python -c "from preprocess_pptx import PPTXProcessor; print('✅ PPTX preprocessing module imported successfully')" 2>/dev/null; then
    echo "✅ PPTX preprocessing module is working"
else
    echo "❌ PPTX preprocessing module import failed"
    echo "Check the preprocess_pptx.py file for syntax errors"
    exit 1
fi

# Run the test suite
echo ""
echo "🧪 Running test suite..."
if python test_pptx_processing.py; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Check the output above."
    exit 1
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📚 Usage examples:"
echo ""
echo "1. Process a single PPTX file:"
echo "   python preprocess_pptx.py your_presentation.pptx -o processed/"
echo ""
echo "2. Process multiple files:"
echo "   python preprocess_pptx.py *.pptx -o processed/"
echo ""
echo "3. Process with verbose output:"
echo "   python preprocess_pptx.py your_file.pptx -o output/ --verbose"
echo ""
echo "4. Generate structured output (JSON + Markdown):"
echo "   python preprocess_pptx.py your_file.pptx -o output/ --format structured"
echo ""
echo "📖 For more information, see README_PPTX_PREPROCESSING.md"
echo ""
echo "🔧 To test with a sample file:"
echo "   1. Place a PPTX file in this directory"
echo "   2. Run: python preprocess_pptx.py your_file.pptx -o test_output/"
echo "   3. Check the generated files in test_output/" 