@echo off
REM Bubu Agent Setup Script for Windows
REM This script sets up the Bubu Agent with virtual environment and configuration

echo 🚀 Setting up Bubu Agent...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python is installed

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📚 Installing dependencies...
pip install -e .
pip install -e ".[dev]"

REM Create environment file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy env.example .env
    echo ✅ .env file created
    echo ⚠️  Please edit .env file with your configuration values
) else (
    echo ✅ .env file already exists
)

REM Run tests to verify installation
echo 🧪 Running tests to verify installation...
python -m pytest tests/ -v --tb=short

echo.
echo 🎉 Bubu Agent setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env file with your configuration:
echo    - GF_NAME: Your girlfriend's name
echo    - GF_WHATSAPP_NUMBER: Her WhatsApp number (E.164 format)
echo    - HF_API_KEY: Your Hugging Face API key
echo    - API_BEARER_TOKEN: A secure token for API access
echo    - WhatsApp provider credentials (Twilio or Meta)
echo.
echo 2. Activate virtual environment:
echo    venv\Scripts\activate
echo.
echo 3. Run the service:
echo    make run
echo.
echo 4. Test the API:
echo    curl http://localhost:8000/healthz
echo    curl http://localhost:8000/dry-run
echo.
echo 📖 For more information, see README.md
echo 🔗 Repository: https://github.com/gkumar2702/bubu_agent
pause
