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

## Quick Start

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
# Install the package in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Or use the Makefile
make install
```

### 4. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp env.example .env
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

## Configuration

### Environment Variables (.env)

```bash
# Core Settings
ENABLED=true
GF_NAME=YourGirlfriendName
GF_WHATSAPP_NUMBER=+1234567890
SENDER_WHATSAPP_NUMBER=+1234567890

# Hugging Face
HF_API_KEY=your_huggingface_api_key
HF_MODEL_ID=Qwen/Qwen2.5-7B-Instruct

# WhatsApp Provider (twilio or meta)
WHATSAPP_PROVIDER=twilio

# Twilio Settings (if using Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+1234567890

# Meta Settings (if using Meta)
META_ACCESS_TOKEN=your_access_token
META_PHONE_NUMBER_ID=your_phone_number_id

# API Security
API_BEARER_TOKEN=your_secure_token

# Optional
TIMEZONE=Asia/Kolkata
DAILY_FLIRTY_TONE=playful
SKIP_DATES=2024-01-01,2024-12-25
```

### Configuration File (config.yaml)

The `config.yaml` file contains message templates, tone settings, and content policies. See the file for detailed configuration options.

## WhatsApp Setup

### Option 1: Twilio WhatsApp

1. **Create Twilio Account**
   - Sign up at [twilio.com](https://www.twilio.com)
   - Get your Account SID and Auth Token

2. **Enable WhatsApp Sandbox**
   - Go to Twilio Console → Messaging → Try it out → Send a WhatsApp message
   - Follow the instructions to join your sandbox
   - Note your WhatsApp number (format: `whatsapp:+1234567890`)

3. **Configure Environment**
   ```bash
   WHATSAPP_PROVIDER=twilio
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_WHATSAPP_FROM=whatsapp:+1234567890
   ```

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
   pip install -e ".[dev]"
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
