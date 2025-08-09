#!/usr/bin/env python3
"""
Switch from Twilio to Meta WhatsApp Cloud API

This script helps you migrate your Bubu Agent configuration
from Twilio to Meta WhatsApp Cloud API.
"""

import os
import shutil
from datetime import datetime

def main():
    print("🔄 Bubu Agent - Switch to Meta WhatsApp")
    print("=" * 50)
    
    # Backup current .env
    if os.path.exists('.env'):
        backup_name = f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        shutil.copy('.env', backup_name)
        print(f"✅ Backed up current .env to {backup_name}")
    
    # Create new .env with Meta configuration
    env_content = """# =============================================================================
# META WHATSAPP CLOUD API SETUP
# =============================================================================

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

# Choose your WhatsApp provider: "meta" (recommended for free tier)
WHATSAPP_PROVIDER=meta

# =============================================================================
# META WHATSAPP CLOUD API SETTINGS (FREE TIER)
# =============================================================================

# Your Meta Access Token (get from Meta Developer Console)
META_ACCESS_TOKEN=your_meta_access_token_here

# Your Meta Phone Number ID (get from Meta Developer Console)
META_PHONE_NUMBER_ID=your_phone_number_id_here

# =============================================================================
# API SECURITY
# =============================================================================

# Secure bearer token for API authentication
API_BEARER_TOKEN=your_secure_bearer_token_here

# =============================================================================
# OPTIONAL SETTINGS
# =============================================================================

# Timezone for scheduling (default: Asia/Kolkata)
TIMEZONE=Asia/Kolkata

# Tone for flirty messages: "playful", "romantic", or "witty"
DAILY_FLIRTY_TONE=playful

# Dates to skip sending messages (YYYY-MM-DD format, comma-separated)
# SKIP_DATES=2024-01-01,2024-12-25

# Log level: "DEBUG", "INFO", "WARNING", "ERROR"
LOG_LEVEL=INFO
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created new .env file configured for Meta WhatsApp")
    
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS:")
    print("=" * 50)
    
    print("\n1. 🏗️  Create Meta Developer Account:")
    print("   Visit: https://developers.facebook.com/apps/")
    print("   Click 'Create App' → 'Business' → 'Next'")
    
    print("\n2. 📱 Add WhatsApp Product:")
    print("   In your app dashboard:")
    print("   Click 'Add Product' → Find 'WhatsApp' → 'Set Up'")
    
    print("\n3. 🔑 Get Your Credentials:")
    print("   - Access Token: WhatsApp → Getting Started")
    print("   - Phone Number ID: WhatsApp → Phone Numbers")
    
    print("\n4. ⚙️  Update .env file:")
    print("   Edit .env and replace:")
    print("   - META_ACCESS_TOKEN=your_actual_token")
    print("   - META_PHONE_NUMBER_ID=your_actual_id")
    print("   - GF_WHATSAPP_NUMBER=+1234567890 (her number)")
    
    print("\n5. 🧪 Test the setup:")
    print("   uvicorn app:app --host 0.0.0.0 --port 8000")
    print("   python interactive_sender.py")
    
    print("\n📖 For detailed instructions, see: FREE_WHATSAPP_APIS.md")
    
    print("\n🎯 Why Meta WhatsApp is better:")
    print("   ✅ 1000 messages/month FREE")
    print("   ✅ No 24-hour window restriction")
    print("   ✅ Direct messaging capability")
    print("   ✅ Production-ready")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
