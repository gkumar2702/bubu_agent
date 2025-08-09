# Bubu Agent

A production-ready Python service that sends personalized WhatsApp messages to your girlfriend three times per day at randomized times.

## ⚠️ Important Ethics Note

**Before using this service, ensure that:**
- The recipient has explicitly consented to receiving automated messages
- You have permission to send messages on their behalf
- The recipient can easily opt out or pause the service
- You respect their privacy and communication preferences

This service includes an easy pause mechanism (set `ENABLED=false` in `.env`) and a `/pause` endpoint for immediate stopping.

## Features

- **Smart Scheduling**: 3 messages per day at randomized times within specified windows
- **AI-Powered Messages**: Uses Hugging Face models for personalized content generation
- **Fallback System**: Template-based fallback when AI generation fails
- **Multiple WhatsApp Providers**: Support for both Twilio and Meta WhatsApp Cloud API
- **Idempotency**: Prevents duplicate messages across restarts
- **Do Not Disturb**: Respects quiet hours (except night messages)
- **Holiday Support**: Skip specific dates via configuration
- **Observability**: Comprehensive logging and health monitoring
- **API Interface**: RESTful API for monitoring and manual control

## Message Schedule

- **Morning**: 06:45–09:30 (sweet + motivational)
- **Flirty**: 12:00–17:30 (playful, respectful)
- **Night**: 21:30–23:30 (sweet + calming)

Each time includes ±20 minutes of randomization and respects do-not-disturb hours (23:45–06:30).

## 🚀 Quick Start

### 📋 Setup Checklist

Before you begin, make sure you have:
- [ ] Python 3.11+ installed
- [ ] A Twilio account (free tier available)
- [ ] A Hugging Face account (free tier available)
- [ ] Your girlfriend's WhatsApp number
- [ ] Her consent to receive automated messages

### 🔧 Quick Setup Commands

```bash
# 1. Clone and setup
git clone https://github.com/gkumar2702/bubu_agent.git
cd bubu_agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate API token
python setup/generate_token.py

# 5. Configure environment
cp setup/env.example .env
# Edit .env with your settings (see detailed setup guide below)

# 6. Run the service
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Option 1: Automated Setup (Recommended)

**On macOS/Linux:**
90601ca56dd1ca3bc9db7d49fb475574```bash
git clone https://github.com/gkumar2702/bubu_agent.git
cd bubu_agent
./setup.sh
```

**On Windows:**
```cmd
git clone https://github.com/gkumar2702/bubu_agent.git
cd bubu_agent
setup.bat
```

### Option 2: Manual Setup

### 1. Clone and Setup

```bash
git clone https://github.com/gkumar2702/bubu_agent.git
cd bubu_agent
```

### 2. Set Up Virtual Environment

**Using Python venv (Recommended):**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Verify activation
python --version
pip --version
```

**Using conda (Alternative):**

```bash
# Create conda environment
conda create -n bubu-agent python=3.12

# Activate conda environment
conda activate bubu-agent

# Verify activation
python --version
pip --version
```

### 3. Install Dependencies

```bash
# Install dependencies from requirements.txt
pip install -r requirements.txt

# Or use the Makefile
make install
```

### 4. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp setup/env.example .env
# Edit .env with your configuration
```

### 5. Run the Service

```bash
# Using uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Or using the Makefile
make run
```

The service will be available at `http://localhost:8000`

### 6. Verify Installation

```bash
# Run tests
make test

# Check health endpoint
curl http://localhost:8000/healthz

# View today's plan
curl http://localhost:8000/plan/today

# Dry run (preview messages)
curl http://localhost:8000/dry-run
```

### 7. Test Your Setup

#### Test API Authentication
```bash
# Test with your bearer token
curl -H "Authorization: Bearer your_actual_token" http://localhost:8000/healthz
```

#### Test WhatsApp Integration
```bash
# Send a test message (replace with your actual token)
curl -X POST "http://localhost:8000/send-now" \
  -H "Authorization: Bearer your_actual_token" \
  -H "Content-Type: application/json" \
  -d '{"type": "morning"}'
```

#### Test Interactive Sender
```bash
# Use the interactive script to preview and send messages
python interactive_sender.py
```

#### Complete Setup Verification
```bash
# 1. Check service health
curl http://localhost:8000/healthz

# 2. Test authentication
curl -H "Authorization: Bearer your_token" http://localhost:8000/healthz

# 3. View today's schedule
curl -H "Authorization: Bearer your_token" http://localhost:8000/plan/today

# 4. Preview messages
curl -H "Authorization: Bearer your_token" http://localhost:8000/dry-run

# 5. Test interactive sender
python interactive_sender.py

# 6. Send a test message
curl -X POST "http://localhost:8000/send-now" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"type": "morning"}'
```

### 8. Common Setup Issues

#### Issue: "Invalid bearer token"
- ✅ Check that your `API_BEARER_TOKEN` in `.env` matches what you're using in requests
- ✅ Ensure there are no extra spaces or quotes around the token
- ✅ Verify the token is at least 32 characters long

#### Issue: "Twilio authentication failed"
- ✅ Verify your `TWILIO_ACCOUNT_SID` starts with `AC`
- ✅ Check that your `TWILIO_AUTH_TOKEN` is correct (click "show" in Twilio console)
- ✅ Ensure your Twilio account is active and has credits

#### Issue: "WhatsApp number not found"
- ✅ Use E.164 format: `+[country code][number]` (e.g., `+1234567890`)
- ✅ If using sandbox, ensure the recipient has joined the sandbox
- ✅ Check that the `TWILIO_WHATSAPP_FROM` includes the `whatsapp:` prefix

#### Issue: "Hugging Face API error"
- ✅ Verify your `HF_API_KEY` is correct
- ✅ Check that your Hugging Face account has API access
- ✅ Ensure the `HF_MODEL_ID` is valid and accessible

## Configuration

### Environment Variables (.env)

```bash
# =============================================================================
# CORE SETTINGS
# =============================================================================

# Enable/disable the service
ENABLED=true

# Your girlfriend's name (used in message personalization)
GF_NAME=YourGirlfriendName

# Your girlfriend's WhatsApp number (E.164 format: +[country code][number])
GF_WHATSAPP_NUMBER=+1234567890

# Your WhatsApp number (for testing and logging)
SENDER_WHATSAPP_NUMBER=+1234567890

# =============================================================================
# HUGGING FACE AI SETTINGS
# =============================================================================

# Your Hugging Face API key (get from https://huggingface.co/settings/tokens)
HF_API_KEY=your_huggingface_api_key

# AI model to use for message generation
HF_MODEL_ID=Qwen/Qwen2.5-7B-Instruct

# =============================================================================
# WHATSAPP PROVIDER SETTINGS
# =============================================================================

# Choose your WhatsApp provider: "twilio" or "meta"
WHATSAPP_PROVIDER=twilio

# =============================================================================
# TWILIO SETTINGS (if using Twilio)
# =============================================================================

# Your Twilio Account SID (starts with "AC")
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Your Twilio Auth Token (get from Twilio Console)
TWILIO_AUTH_TOKEN=your_auth_token_here

# Twilio WhatsApp number (include "whatsapp:" prefix)
# For sandbox: whatsapp:+14155238886
# For production: whatsapp:+1234567890
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# =============================================================================
# META SETTINGS (if using Meta WhatsApp Cloud API)
# =============================================================================

# Your Meta Access Token
META_ACCESS_TOKEN=your_access_token

# Your Meta Phone Number ID
META_PHONE_NUMBER_ID=your_phone_number_id

# =============================================================================
# API SECURITY
# =============================================================================

# Secure bearer token for API authentication (generate a strong token)
API_BEARER_TOKEN=your_secure_bearer_token_here

# =============================================================================
# OPTIONAL SETTINGS
# =============================================================================

# Timezone for scheduling (default: Asia/Kolkata)
TIMEZONE=Asia/Kolkata

# Tone for flirty messages: "playful", "romantic", or "witty"
DAILY_FLIRTY_TONE=playful

# Dates to skip sending messages (YYYY-MM-DD format, comma-separated)
SKIP_DATES=2024-01-01,2024-12-25

# Log level: "DEBUG", "INFO", "WARNING", "ERROR"
LOG_LEVEL=INFO
```

### Configuration File (config.yaml)

The `config.yaml` file contains message templates, tone settings, and content policies. See the file for detailed configuration options.

## Detailed Setup Guide

### 🔐 API Bearer Token Setup

The API Bearer Token is used to secure your endpoints and authenticate API requests.

#### Step 1: Generate a Secure Token

**Option A: Use the Built-in Generator (Recommended)**
```bash
# Run the token generator script
python setup/generate_token.py
```

**Option B: Use a Password Generator**
```bash
# Generate a secure 32-character token
openssl rand -base64 32
```

**Option C: Use Python**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**Option D: Use Online Generator**
- Visit [https://generate-secret.vercel.app/32](https://generate-secret.vercel.app/32)
- Copy the generated token

#### Step 2: Configure the Token

1. **Edit your `.env` file:**
   ```bash
   nano .env
   # or
   code .env
   ```

2. **Replace the placeholder:**
   ```bash
   # Change this line:
   API_BEARER_TOKEN=your_secure_bearer_token_here
   
   # To something like:
   API_BEARER_TOKEN=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890
   ```

3. **Test the token:**
   ```bash
   curl -H "Authorization: Bearer your_actual_token" http://localhost:8000/healthz
   ```

#### Security Best Practices

- ✅ **Use a strong token**: At least 32 characters, mix of letters, numbers, symbols
- ✅ **Keep it secret**: Never commit your `.env` file to version control
- ✅ **Rotate regularly**: Change the token periodically
- ✅ **Use HTTPS**: In production, always use HTTPS for API calls
- ❌ **Don't share**: Never share your token publicly
- ❌ **Don't reuse**: Use different tokens for different environments

### 📱 Twilio WhatsApp Setup

#### Step 1: Create Twilio Account

1. **Sign up for Twilio:**
   - Visit [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
   - Click "Sign up for free"
   - Fill in your details and verify your email

2. **Verify your phone number:**
   - Twilio will send a verification code to your phone
   - Enter the code to complete verification

3. **Get your credentials:**
   - Go to [Twilio Console](https://console.twilio.com/)
   - Note your **Account SID** (starts with `AC...`)
   - Note your **Auth Token** (click "show" to reveal)

#### Step 2: Set Up WhatsApp Sandbox

1. **Access WhatsApp Sandbox:**
   - In Twilio Console, go to **Messaging** → **Try it out** → **Send a WhatsApp message**
   - Or visit: [https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn)

2. **Join the Sandbox:**
   - You'll see a WhatsApp number and a join code
   - Example: `+1 415 523 8886` with code `join <two-words>`
   - Open WhatsApp on your phone
   - Send the join message to the number: `join <two-words>`
   - You'll receive a confirmation message

3. **Test the Sandbox:**
   - In the Twilio console, try sending a test message
   - Enter your WhatsApp number (with country code)
   - Send a test message
   - You should receive it on your phone

#### Step 3: Configure Bubu Agent

1. **Update your `.env` file:**
   ```bash
   # WhatsApp Provider
   WHATSAPP_PROVIDER=twilio
   
   # Twilio Credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   
   # Your girlfriend's WhatsApp number (with country code)
   GF_WHATSAPP_NUMBER=+1234567890
   
   # Your WhatsApp number (for testing)
   SENDER_WHATSAPP_NUMBER=+1234567890
   ```

2. **Test the configuration:**
   ```bash
   # Start the service
   uvicorn app:app --host 0.0.0.0 --port 8000
   
   # Test sending a message
   curl -X POST "http://localhost:8000/send-now" \
     -H "Authorization: Bearer your_api_token" \
     -H "Content-Type: application/json" \
     -d '{"type": "morning"}'
   ```

#### Step 4: Production Setup (Optional)

For production use, you'll need to:

1. **Request WhatsApp Business API:**
   - Go to [Twilio WhatsApp Business API](https://www.twilio.com/whatsapp)
   - Apply for a business number
   - Complete the verification process

2. **Update configuration:**
   ```bash
   # Replace sandbox number with your business number
   TWILIO_WHATSAPP_FROM=whatsapp:+1234567890
   ```

#### Troubleshooting Twilio

**Issue: "Message not delivered"**
- ✅ Check that your girlfriend's number is in the correct format: `+1234567890`
- ✅ Ensure she has joined the sandbox (if using sandbox)
- ✅ Verify your Twilio account has sufficient credits

**Issue: "Authentication failed"**
- ✅ Double-check your Account SID and Auth Token
- ✅ Make sure there are no extra spaces in your `.env` file
- ✅ Verify your Twilio account is active

**Issue: "Invalid phone number"**
- ✅ Use E.164 format: `+[country code][number]`
- ✅ Example: `+1234567890` for US, `+447123456789` for UK
- ✅ Remove any spaces, dashes, or parentheses

#### WhatsApp Sandbox Limitations

- ⏰ **24-hour window**: Recipients must respond within 24 hours to continue receiving messages
- 📱 **One-way initially**: First message must be initiated by the recipient
- 🔄 **Session renewal**: Recipients need to send a message to renew the session
- 💰 **Free tier limits**: Check Twilio's current free tier limits

### Option 2: Meta WhatsApp Cloud API

1. **Create Meta App**
   - Go to [developers.facebook.com](https://developers.facebook.com)
   - Create a new app
   - Add WhatsApp product to your app

2. **Configure WhatsApp**
   - Set up your phone number
   - Get your Access Token and Phone Number ID
   - Configure webhooks (optional)

3. **Configure Environment**
   ```bash
   WHATSAPP_PROVIDER=meta
   META_ACCESS_TOKEN=your_access_token
   META_PHONE_NUMBER_ID=your_phone_number_id
   ```

## Hugging Face Setup

1. **Get API Key**
   - Sign up at [huggingface.co](https://huggingface.co)
   - Go to Settings → Access Tokens
   - Create a new token

2. **Choose Model**
   - Recommended: `Qwen/Qwen2.5-7B-Instruct`
   - Alternative: `microsoft/DialoGPT-medium` or similar

3. **Configure Environment**
   ```bash
   HF_API_KEY=your_api_key
   HF_MODEL_ID=Qwen/Qwen2.5-7B-Instruct
   ```

## API Endpoints

### Health Check
```bash
GET /healthz
```

### Today's Plan
```bash
GET /plan/today
```

### Dry Run (Preview Messages)
```bash
GET /dry-run
```

### Send Message Now
```bash
POST /send-now
Authorization: Bearer your_token
Content-Type: application/json

{
  "type": "morning"
}
```

### Message Preview
```bash
POST /config/preview
Authorization: Bearer your_token
Content-Type: application/json

{
  "type": "morning",
  "options": {"use_fallback": true}
}
```

### Recent Messages
```bash
GET /messages/recent?days=7
Authorization: Bearer your_token
```

### Pause Service
```bash
POST /pause
Authorization: Bearer your_token
```

## Development

### Setting Up Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gkumar2702/bubu_agent.git
   cd bubu_agent
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up pre-commit hooks (optional):**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
pytest tests/test_compose.py -v

# Run tests with verbose output
pytest tests/ -v --tb=short
```

### Code Quality

```bash
# Linting
make lint

# Code formatting
make format

# Check formatting
make check

# Type checking
mypy .
```

### Clean Up

```bash
# Clean generated files
make clean

# Remove virtual environment
deactivate
rm -rf venv/
```

### Pre-commit Hooks

The project includes pre-commit hooks for code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks on all files
pre-commit run --all-files
```

## Production Deployment

### Using Docker

1. **Build Image**
   ```bash
   make docker-build
   ```

2. **Run Container**
   ```bash
   make docker-run
   ```

3. **Using Docker Compose (Recommended)**

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  bubu-agent:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:
```bash
docker-compose up -d
```

### Using Docker Hub

```bash
# Pull the image
docker pull gkumar2702/bubu-agent:latest

# Run the container
docker run -p 8000:8000 --env-file .env gkumar2702/bubu-agent:latest
```

### Using Systemd

Create a systemd service file:

```ini
[Unit]
Description=Bubu Agent
After=network.target

[Service]
Type=simple
User=bubu
WorkingDirectory=/path/to/bubu_agent
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Using PM2

```bash
pm2 start "uvicorn app:app --host 0.0.0.0 --port 8000" --name bubu-agent
pm2 save
pm2 startup
```

## Monitoring and Logging

The service provides comprehensive logging with structured JSON logs. Key log events include:

- Message composition and sending
- Schedule generation
- Provider responses
- Error handling

Logs are scrubbed of sensitive information (API keys, phone numbers) for security.

## Troubleshooting

### Common Issues

1. **Messages not sending**
   - Check WhatsApp provider configuration
   - Verify phone numbers are in E.164 format
   - Check provider API limits

2. **AI generation failing**
   - Verify Hugging Face API key
   - Check model availability
   - Review fallback templates

3. **Scheduling issues**
   - Verify timezone configuration
   - Check skip dates
   - Review do-not-disturb settings

### Debug Mode

Set log level to DEBUG in `.env`:
```bash
LOG_LEVEL=DEBUG
```

## Security Considerations

- Store API keys securely
- Use strong bearer tokens
- Regularly rotate credentials
- Monitor for unusual activity
- Respect recipient privacy

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/bubu_agent.git
   cd bubu_agent
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

5. **Run tests and quality checks**
   ```bash
   make test
   make lint
   make format
   ```

6. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

7. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

### Automated Testing

- **Triggered on:** Push to main/develop branches and pull requests
- **Python versions:** 3.11, 3.12
- **Tests:** Unit tests, integration tests, security checks
- **Coverage:** Code coverage reporting with Codecov

### Automated Deployment

- **Triggered on:** Tagged releases (v*)
- **Docker:** Automatic Docker image building and pushing
- **Releases:** Automatic GitHub releases

### Workflow Status

[![Test Bubu Agent](https://github.com/gkumar2702/bubu_agent/workflows/Test%20Bubu%20Agent/badge.svg)](https://github.com/gkumar2702/bubu_agent/actions)
[![Deploy Bubu Agent](https://github.com/gkumar2702/bubu_agent/workflows/Deploy%20Bubu%20Agent/badge.svg)](https://github.com/gkumar2702/bubu_agent/actions)

### Local Development with CI

To ensure your changes pass CI:

```bash
# Set up virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run the same checks as CI
make lint
make test
make test-cov
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs
3. Open an issue on GitHub

---

**Remember**: Always ensure the recipient has consented to automated messages and provide easy opt-out mechanisms.
