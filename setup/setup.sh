#!/bin/bash

# Bubu Agent Setup Script
# This script sets up the Bubu Agent with virtual environment and configuration

set -e

echo "🚀 Setting up Bubu Agent..."

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.11 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp setup/env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env file with your configuration values"
else
    echo "✅ .env file already exists"
fi

# Run tests to verify installation
echo "🧪 Running tests to verify installation..."
python -m pytest tests/ -v --tb=short

echo ""
echo "🎉 Bubu Agent setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your configuration:"
echo "   - GF_NAME: Your girlfriend's name"
echo "   - GF_WHATSAPP_NUMBER: Her WhatsApp number (E.164 format)"
echo "   - HF_API_KEY: Your Hugging Face API key"
echo "   - API_BEARER_TOKEN: A secure token for API access"
echo "   - WhatsApp provider credentials (Twilio or Meta)"
echo ""
echo "2. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the service:"
echo "   make run"
echo ""
echo "4. Test the API:"
echo "   curl http://localhost:8000/healthz"
echo "   curl http://localhost:8000/dry-run"
echo ""
echo "📖 For more information, see README.md"
echo "🔗 Repository: https://github.com/gkumar2702/bubu_agent"
