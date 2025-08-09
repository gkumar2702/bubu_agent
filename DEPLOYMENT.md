# Bubu Agent - Deployment Guide

## 🚀 Quick Deployment

### Automated Setup (Recommended)

**macOS/Linux:**
```bash
git clone https://github.com/gkumar2702/bubu_agent.git
cd bubu_agent
./setup.sh
```

**Windows:**
```cmd
git clone https://github.com/gkumar2702/bubu_agent.git
cd bubu_agent
setup.bat
```

## 📋 Prerequisites

- Python 3.11 or higher
- Git
- WhatsApp Business API access (Twilio or Meta)
- Hugging Face API key

## 🔧 Environment Setup

### 1. Virtual Environment

**Create and activate virtual environment:**

```bash
# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### 3. Configuration

Copy and configure the environment file:

```bash
cp env.example .env
# Edit .env with your credentials
```

**Required environment variables:**
- `GF_NAME`: Your girlfriend's name
- `GF_WHATSAPP_NUMBER`: Her WhatsApp number (E.164 format)
- `HF_API_KEY`: Hugging Face API key
- `API_BEARER_TOKEN`: Secure token for API access
- WhatsApp provider credentials (Twilio or Meta)

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f bubu-agent

# Stop services
docker-compose down
```

### Using Docker directly

```bash
# Build image
docker build -t bubu-agent .

# Run container
docker run -p 8000:8000 --env-file .env bubu-agent
```

## 🚀 Production Deployment

### Using Systemd

Create `/etc/systemd/system/bubu-agent.service`:

```ini
[Unit]
Description=Bubu Agent
After=network.target

[Service]
Type=simple
User=bubu
WorkingDirectory=/opt/bubu_agent
Environment=PATH=/opt/bubu_agent/venv/bin
ExecStart=/opt/bubu_agent/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable bubu-agent
sudo systemctl start bubu-agent
sudo systemctl status bubu-agent
```

### Using PM2

```bash
# Install PM2
npm install -g pm2

# Start application
pm2 start "uvicorn app:app --host 0.0.0.0 --port 8000" --name bubu-agent

# Save PM2 configuration
pm2 save
pm2 startup
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

The project includes two main workflows:

1. **Test Workflow** (`.github/workflows/test.yml`)
   - Triggers: Push to main/develop, pull requests
   - Tests: Python 3.11, 3.12
   - Includes: Unit tests, integration tests, security checks
   - Coverage: Codecov integration

2. **Deploy Workflow** (`.github/workflows/deploy.yml`)
   - Triggers: Tagged releases (v*)
   - Actions: Docker build, GitHub release, Docker Hub push

### Workflow Status Badges

```markdown
[![Test Bubu Agent](https://github.com/gkumar2702/bubu_agent/workflows/Test%20Bubu%20Agent/badge.svg)](https://github.com/gkumar2702/bubu_agent/actions)
[![Deploy Bubu Agent](https://github.com/gkumar2702/bubu_agent/workflows/Deploy%20Bubu%20Agent/badge.svg)](https://github.com/gkumar2702/bubu_agent/actions)
```

## 🧪 Testing

### Run Tests Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
pytest tests/test_compose.py -v
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/healthz

# Today's plan
curl http://localhost:8000/plan/today

# Dry run (preview messages)
curl http://localhost:8000/dry-run

# Send message (requires authentication)
curl -X POST http://localhost:8000/send-now \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "morning"}'
```

## 🔍 Monitoring

### Health Checks

The application provides a health endpoint at `/healthz` that returns:

```json
{
  "status": "healthy|degraded|unhealthy",
  "enabled": true,
  "provider": "twilio|meta",
  "timezone": "Asia/Kolkata"
}
```

### Logging

Structured JSON logging with PII scrubbing:

```bash
# View logs
tail -f logs/bubu_agent.log

# Docker logs
docker-compose logs -f bubu-agent
```

### Database

SQLite database for message tracking:

```bash
# View database
sqlite3 bubu_agent.db

# Backup database
cp bubu_agent.db backup_$(date +%Y%m%d).db
```

## 🔒 Security

### Environment Variables

- Store sensitive data in `.env` file
- Never commit `.env` to version control
- Use strong API tokens
- Rotate credentials regularly

### API Security

- Bearer token authentication for sensitive endpoints
- Rate limiting (implement if needed)
- Input validation and sanitization
- PII protection in logs

## 📊 Performance

### Optimization Tips

1. **Database**: SQLite is sufficient for small deployments
2. **Caching**: Consider Redis for high-traffic scenarios
3. **Scaling**: Use load balancer for multiple instances
4. **Monitoring**: Implement metrics collection

### Resource Requirements

- **CPU**: 1 core minimum, 2 cores recommended
- **Memory**: 512MB minimum, 1GB recommended
- **Storage**: 100MB for application + database
- **Network**: Outbound HTTPS for API calls

## 🆘 Troubleshooting

### Common Issues

1. **Import errors**: Ensure virtual environment is activated
2. **API failures**: Check credentials and network connectivity
3. **Database errors**: Verify file permissions and disk space
4. **Scheduling issues**: Check timezone configuration

### Debug Mode

```bash
# Set debug logging
export LOG_LEVEL=DEBUG

# Run with debug output
uvicorn app:app --host 0.0.0.0 --port 8000 --log-level debug
```

### Support

- Check the [README.md](README.md) for detailed documentation
- Review [GitHub Issues](https://github.com/gkumar2702/bubu_agent/issues)
- Ensure the recipient has consented to automated messages

## 📈 Scaling

### Horizontal Scaling

For high-availability deployments:

1. **Load Balancer**: Use nginx or HAProxy
2. **Multiple Instances**: Deploy across multiple servers
3. **Database**: Consider PostgreSQL for shared state
4. **Caching**: Implement Redis for session management

### Vertical Scaling

For increased performance:

1. **Resources**: Increase CPU and memory allocation
2. **Optimization**: Profile and optimize bottlenecks
3. **Caching**: Implement application-level caching
4. **Database**: Optimize queries and indexes

---

**Remember**: Always ensure the recipient has consented to automated messages and provide easy opt-out mechanisms.
