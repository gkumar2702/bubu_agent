#!/usr/bin/env python3
"""
Switch to Ultramsg WhatsApp API

This script helps you configure Bubu Agent to use Ultramsg
WhatsApp API instead of other providers.
"""

import os
import shutil
from datetime import datetime

def main():
    print("🔄 Bubu Agent - Switch to Ultramsg WhatsApp")
    print("=" * 50)
    
    # Backup current .env
    if os.path.exists('.env'):
        backup_name = f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        shutil.copy('.env', backup_name)
        print(f"✅ Backed up current .env to {backup_name}")
    
    # Create new .env with Ultramsg configuration
    env_content = """# =============================================================================
# ULTRAMSG WHATSAPP API SETUP
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
HF_MODEL_ID=openai/gpt-oss-20b

# =============================================================================
# WHATSAPP PROVIDER SETTINGS
# =============================================================================

# Choose your WhatsApp provider: "ultramsg" (recommended for free tier)
WHATSAPP_PROVIDER=ultramsg

# =============================================================================
# ULTRAMSG WHATSAPP API SETTINGS (FREE TIER)
# =============================================================================

# Your Ultramsg API Key (get from ultramsg.com dashboard)
ULTRAMSG_API_KEY=your_ultramsg_api_key_here

# Your Ultramsg Instance ID (get from ultramsg.com dashboard)
ULTRAMSG_INSTANCE_ID=your_ultramsg_instance_id_here

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
    
    print("✅ Created new .env file configured for Ultramsg WhatsApp")
    
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS:")
    print("=" * 50)
    
    print("\n1. 🌐 Create Ultramsg Account:")
    print("   Visit: https://ultramsg.com")
    print("   Click 'Sign Up' and create your account")
    
    print("\n2. 📱 Set Up WhatsApp Instance:")
    print("   In your Ultramsg dashboard:")
    print("   - Click 'Add Instance'")
    print("   - Choose 'WhatsApp'")
    print("   - Follow the QR code setup")
    
    print("\n3. 🔑 Get Your Credentials:")
    print("   - API Key: Dashboard → API → Copy your API key")
    print("   - Instance ID: Dashboard → Instances → Copy Instance ID")
    
    print("\n4. ⚙️  Update .env file:")
    print("   Edit .env and replace:")
    print("   - ULTRAMSG_API_KEY=your_actual_api_key")
    print("   - ULTRAMSG_INSTANCE_ID=your_actual_instance_id")
    print("   - GF_WHATSAPP_NUMBER=+1234567890 (her number)")
    
    print("\n5. 🧪 Test the setup:")
    print("   uvicorn setup.app:app --host 0.0.0.0 --port 8000")
    print("   python interactive_sender.py")
    
    print("\n📖 For detailed instructions, see: ULTRAMSG_SETUP_GUIDE.md")
    
    print("\n🎯 Why Ultramsg is great:")
    print("   ✅ Free tier available")
    print("   ✅ Simple setup process")
    print("   ✅ Good documentation")
    print("   ✅ Reliable delivery")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
