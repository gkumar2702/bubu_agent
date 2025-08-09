# Ultramsg WhatsApp API Setup Guide

## 🌟 Why Choose Ultramsg?

**✅ Advantages:**
- **Free tier available** with generous limits
- **Simple setup process** - no complex verification
- **Direct messaging** - no 24-hour window restrictions
- **Good documentation** and support
- **Reliable delivery** and uptime
- **Multi-platform support**

## 📋 Prerequisites

Before starting, make sure you have:
- ✅ A smartphone with WhatsApp installed
- ✅ A stable internet connection
- ✅ Access to your phone for QR code scanning
- ✅ Your girlfriend's WhatsApp number (with country code)

## 🚀 Step-by-Step Setup

### Step 1: Create Ultramsg Account

1. **Visit Ultramsg Website:**
   - Go to [https://ultramsg.com](https://ultramsg.com)
   - Click "Sign Up" or "Get Started"

2. **Fill in Registration:**
   - Enter your email address
   - Choose a strong password
   - Verify your email (check spam folder)

3. **Complete Profile:**
   - Add your name and phone number
   - Verify your phone number if required

### Step 2: Set Up WhatsApp Instance

1. **Access Dashboard:**
   - Log in to your Ultramsg account
   - You'll see the main dashboard

2. **Create New Instance:**
   - Click "Add Instance" or "Create Instance"
   - Select "WhatsApp" as the platform
   - Give your instance a name (e.g., "Bubu Agent")

3. **QR Code Setup:**
   - A QR code will appear on screen
   - Open WhatsApp on your phone
   - Go to Settings → Linked Devices → Link a Device
   - Scan the QR code with your phone
   - Wait for the connection to establish

4. **Verify Connection:**
   - You should see "Connected" status
   - Your phone number will appear in the instance
   - Test by sending a message to yourself

### Step 3: Get Your API Credentials

1. **Find Your API Key:**
   - In the dashboard, go to "API" section
   - Copy your API key (it looks like: `abc123def456ghi789...`)
   - Keep this secure - don't share it

2. **Get Your Instance ID:**
   - Go to "Instances" section
   - Find your WhatsApp instance
   - Copy the Instance ID (it looks like: `1234567890`)

3. **Test API Connection:**
   - Use the API testing tool in the dashboard
   - Send a test message to verify everything works

### Step 4: Configure Bubu Agent

1. **Switch to Ultramsg Configuration:**
   ```bash
   python setup/switch_to_ultramsg.py
   ```

2. **Edit Your .env File:**
   ```bash
   nano .env
   # or
   code .env
   ```

3. **Update the Configuration:**
   ```bash
   # Replace these values with your actual credentials:
   ULTRAMSG_API_KEY=your_actual_api_key_here
   ULTRAMSG_INSTANCE_ID=your_actual_instance_id_here
   GF_WHATSAPP_NUMBER=+1234567890  # Your girlfriend's number
   ```

4. **Generate API Bearer Token:**
   ```bash
   python setup/generate_token.py
   # Copy the generated token to API_BEARER_TOKEN in .env
   ```

### Step 5: Test Your Setup

1. **Start the Server:**
   ```bash
   uvicorn setup.app:app --host 0.0.0.0 --port 8000
   ```

2. **Test Health Endpoint:**
   ```bash
   curl http://localhost:8000/healthz
   ```

3. **Test Interactive Sender:**
   ```bash
   python interactive_sender.py
   ```

4. **Send a Test Message:**
   ```bash
   curl -X POST "http://localhost:8000/send-now" \
     -H "Authorization: Bearer your_token" \
     -H "Content-Type: application/json" \
     -d '{"type": "morning"}'
   ```

## 🔧 Configuration Examples

### Complete .env File Example:
```bash
# =============================================================================
# CORE SETTINGS
# =============================================================================
ENABLED=true
GF_NAME=Sarah
GF_WHATSAPP_NUMBER=+1234567890
SENDER_WHATSAPP_NUMBER=+1234567890

# =============================================================================
# HUGGING FACE AI SETTINGS
# =============================================================================
HF_API_KEY=your_huggingface_api_key
HF_MODEL_ID=Qwen/Qwen2.5-7B-Instruct

# =============================================================================
# WHATSAPP PROVIDER SETTINGS
# =============================================================================
WHATSAPP_PROVIDER=ultramsg

# =============================================================================
# ULTRAMSG WHATSAPP API SETTINGS
# =============================================================================
ULTRAMSG_API_KEY=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890
ULTRAMSG_INSTANCE_ID=1234567890

# =============================================================================
# API SECURITY
# =============================================================================
API_BEARER_TOKEN=your_secure_bearer_token_here

# =============================================================================
# OPTIONAL SETTINGS
# =============================================================================
TIMEZONE=Asia/Kolkata
DAILY_FLIRTY_TONE=playful
LOG_LEVEL=INFO
```

## 🆘 Troubleshooting

### Issue: "Instance not connected"
- ✅ Check if your phone has internet connection
- ✅ Ensure WhatsApp is open and active
- ✅ Try re-scanning the QR code
- ✅ Restart the Ultramsg instance

### Issue: "API key invalid"
- ✅ Copy the API key exactly from the dashboard
- ✅ Check for extra spaces or characters
- ✅ Verify your account is active

### Issue: "Message not delivered"
- ✅ Ensure the recipient number is in E.164 format (+1234567890)
- ✅ Check if the recipient has WhatsApp
- ✅ Verify your instance is connected and active

### Issue: "Instance ID not found"
- ✅ Copy the Instance ID from the Instances section
- ✅ Make sure you're using the correct instance
- ✅ Check if the instance is active

## 📊 Ultramsg Pricing

### Free Tier:
- ✅ **100 messages/day**
- ✅ **Basic features**
- ✅ **Standard support**

### Paid Plans:
- **Starter**: $9/month - 1000 messages/day
- **Professional**: $29/month - 5000 messages/day
- **Enterprise**: Custom pricing

## 🔒 Security Best Practices

1. **Keep API Key Secret:**
   - Never share your API key publicly
   - Don't commit it to version control
   - Use environment variables

2. **Regular Monitoring:**
   - Check your Ultramsg dashboard regularly
   - Monitor message delivery status
   - Review usage statistics

3. **Backup Configuration:**
   - Keep backup of your .env file
   - Store credentials securely
   - Document your setup process

## 🎯 Tips for Success

1. **Test Thoroughly:**
   - Send test messages to yourself first
   - Verify message delivery
   - Check message formatting

2. **Monitor Performance:**
   - Use the interactive sender for testing
   - Check logs for any errors
   - Monitor API response times

3. **Keep Updated:**
   - Check Ultramsg documentation regularly
   - Update your Bubu Agent when new versions are available
   - Monitor for any API changes

## 📞 Support

If you encounter issues:

1. **Check Ultramsg Documentation:**
   - [Ultramsg API Docs](https://ultramsg.com/docs)
   - [Ultramsg Support](https://ultramsg.com/support)

2. **Bubu Agent Support:**
   - Check the troubleshooting section
   - Review the logs for error messages
   - Open an issue on GitHub

3. **Community Help:**
   - Join Ultramsg community forums
   - Check GitHub issues for similar problems

---

**🎉 Congratulations! You're now ready to send WhatsApp messages via Ultramsg!**

**Next Steps:**
1. Test your setup with the interactive sender
2. Configure your girlfriend's phone number
3. Set up automatic scheduling
4. Enjoy sending personalized messages! 💕
