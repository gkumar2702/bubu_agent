# Free WhatsApp APIs - Complete Setup Guide

## 🚫 Why Twilio Free Tier is Limited

Twilio's free tier for WhatsApp has severe limitations:
- ❌ **24-hour window**: Recipients must respond within 24 hours
- ❌ **One-way initially**: First message must be initiated by recipient
- ❌ **Session renewal**: Recipients need to send messages to renew
- ❌ **Limited messages**: Very restricted message count
- ❌ **Sandbox only**: No production use without paid plan

## 🆓 Free WhatsApp API Alternatives

### 1. **Meta WhatsApp Cloud API** (Recommended)

**✅ Advantages:**
- **1000 messages/month FREE**
- **No 24-hour window restriction**
- **Direct messaging capability**
- **Production-ready**
- **Easy setup**

**📋 Setup Steps:**

#### Step 1: Create Meta Developer Account
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click "Get Started" or "Log In"
3. Create a new app (choose "Business" type)

#### Step 2: Add WhatsApp Product
1. In your app dashboard, click "Add Product"
2. Find "WhatsApp" and click "Set Up"
3. Follow the setup wizard

#### Step 3: Get Your Credentials
1. **Access Token**: Go to WhatsApp → Getting Started
2. **Phone Number ID**: Go to WhatsApp → Phone Numbers
3. **Verify your phone number**

#### Step 4: Configure Bubu Agent
```bash
# Update your .env file
WHATSAPP_PROVIDER=meta
META_ACCESS_TOKEN=your_access_token_here
META_PHONE_NUMBER_ID=your_phone_number_id_here
```

### 2. **Ultramsg API** (Alternative)

**✅ Advantages:**
- **Free tier available**
- **Simple setup**
- **Good documentation**

**📋 Setup:**
1. Sign up at [ultramsg.com](https://ultramsg.com)
2. Get your API key
3. Configure in Bubu Agent

### 3. **WAMR API** (Alternative)

**✅ Advantages:**
- **Free messages available**
- **Multi-platform support**

**📋 Setup:**
1. Visit [wamr.app](https://wamr.app)
2. Create account and get API key
3. Configure in Bubu Agent

## 🔧 Quick Setup for Meta WhatsApp

### 1. Create Meta App
```bash
# Visit: https://developers.facebook.com/apps/
# Click "Create App" → "Business" → "Next"
# Fill in app details
```

### 2. Add WhatsApp
```bash
# In your app dashboard:
# 1. Click "Add Product"
# 2. Find "WhatsApp" → "Set Up"
# 3. Follow the wizard
```

### 3. Get Credentials
```bash
# Access Token:
# WhatsApp → Getting Started → Copy "Access Token"

# Phone Number ID:
# WhatsApp → Phone Numbers → Copy "Phone Number ID"
```

### 4. Update Configuration
```bash
# Copy the new environment file
cp setup/env.meta.example .env

# Edit .env with your actual values:
META_ACCESS_TOKEN=your_actual_access_token
META_PHONE_NUMBER_ID=your_actual_phone_number_id
GF_WHATSAPP_NUMBER=+1234567890  # Your girlfriend's number
```

### 5. Test Setup
```bash
# Restart the server
uvicorn setup.app:app --host 0.0.0.0 --port 8000

# Test sending a message
curl -X POST "http://localhost:8000/send-now" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"type": "morning"}'
```

## 📱 Meta WhatsApp Features

### Free Tier Limits:
- ✅ **1000 messages/month**
- ✅ **No time restrictions**
- ✅ **Direct messaging**
- ✅ **Media support**
- ✅ **Template messages**

### Message Types:
- **Text messages**: Unlimited
- **Media messages**: Images, videos, documents
- **Template messages**: Pre-approved templates
- **Interactive messages**: Buttons, lists

## 🔒 Security Best Practices

1. **Keep tokens secret**: Never share your access tokens
2. **Use environment variables**: Store credentials in `.env`
3. **Rotate tokens**: Change tokens periodically
4. **Monitor usage**: Check your Meta app dashboard regularly

## 🆘 Troubleshooting

### "Invalid access token"
- ✅ Check your access token is correct
- ✅ Ensure token hasn't expired
- ✅ Verify app permissions

### "Phone number not found"
- ✅ Use E.164 format: `+[country code][number]`
- ✅ Ensure recipient has WhatsApp
- ✅ Check phone number is verified

### "Message not delivered"
- ✅ Verify your Meta app is active
- ✅ Check message content compliance
- ✅ Ensure recipient hasn't blocked you

## 📊 Cost Comparison

| Service | Free Tier | Paid Plans | Best For |
|---------|-----------|------------|----------|
| **Meta WhatsApp** | 1000 msg/month | $0.005/msg | Production use |
| **Twilio** | Sandbox only | $0.005/msg | Enterprise |
| **Ultramsg** | Limited free | $0.01/msg | Simple setup |
| **WAMR** | Limited free | $0.008/msg | Multi-platform |

## 🎯 Recommendation

**Use Meta WhatsApp Cloud API** because:
- ✅ **Most generous free tier**
- ✅ **No time restrictions**
- ✅ **Production-ready**
- ✅ **Easy setup**
- ✅ **Reliable delivery**

---

**Ready to switch? Follow the Meta WhatsApp setup guide above! 🚀**
