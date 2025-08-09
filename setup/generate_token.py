#!/usr/bin/env python3
"""
Generate a secure API Bearer Token for Bubu Agent.

This script helps you create a strong, secure token for API authentication.
"""

import secrets
import string
import sys

def generate_secure_token(length=32):
    """Generate a secure random token."""
    # Use URL-safe base64 encoding for better compatibility
    return secrets.token_urlsafe(length)

def generate_readable_token(length=32):
    """Generate a readable token (letters and numbers only)."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("🔐 Bubu Agent - API Token Generator")
    print("=" * 40)
    
    # Generate different types of tokens
    print("\n1. URL-Safe Token (Recommended):")
    url_safe_token = generate_secure_token(32)
    print(f"   {url_safe_token}")
    
    print("\n2. Readable Token (Letters & Numbers):")
    readable_token = generate_readable_token(32)
    print(f"   {readable_token}")
    
    print("\n3. Extra Long Token (64 characters):")
    long_token = generate_secure_token(64)
    print(f"   {long_token}")
    
    print("\n" + "=" * 40)
    print("📝 Instructions:")
    print("1. Copy one of the tokens above")
    print("2. Open your .env file")
    print("3. Replace the API_BEARER_TOKEN line with:")
    print(f"   API_BEARER_TOKEN={url_safe_token}")
    print("\n4. Save the .env file")
    print("5. Restart your Bubu Agent")
    
    print("\n🔒 Security Tips:")
    print("✅ Use the URL-safe token for best compatibility")
    print("✅ Keep your token secret - never share it")
    print("✅ Don't commit your .env file to version control")
    print("✅ Change your token periodically")
    
    print("\n🧪 Test your token:")
    print("curl -H 'Authorization: Bearer YOUR_TOKEN' http://localhost:8000/healthz")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
