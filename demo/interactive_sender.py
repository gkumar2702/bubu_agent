#!/usr/bin/env python3
"""
Interactive Message Sender for Bubu Agent

This script allows you to:
1. View 5 message options for each type (morning, flirty, night)
2. Select and send messages immediately
3. Preview messages before sending
"""

import asyncio
import httpx
import json
import sys
from typing import List, Dict, Any
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the project root
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

class InteractiveSender:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        # Increase timeout to handle slow AI generation
        self.client = httpx.AsyncClient(timeout=120.0)
        self.bearer_token = os.getenv("API_BEARER_TOKEN", "your_secure_bearer_token_here")
        
        # Debug: Check if token was loaded correctly
        if self.bearer_token == "your_secure_bearer_token_here":
            print("⚠️  Warning: Using default bearer token. Check if .env file exists and contains API_BEARER_TOKEN")
        else:
            print(f"✅ Bearer token loaded: {self.bearer_token[:8]}...{self.bearer_token[-4:]}")
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get_message_options(self, message_type: str, use_ai: bool = False) -> List[Dict[str, Any]]:
        """Get 5 message options for a specific type."""
        try:
            # Use the config preview endpoint to get message options
            generation_type = "AI-generated" if use_ai else "fallback templates"
            print(f"   Generating {generation_type} messages...")
            
            response = await self.client.post(
                f"{self.base_url}/config/preview",
                json={
                    "type": message_type,
                    "options": {
                        "count": 5,
                        "include_fallback": True,
                        "randomize": True,
                        "use_ai_generation": use_ai
                    }
                },
                headers={"Authorization": f"Bearer {self.bearer_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("messages", [])
            else:
                print(f"❌ Error getting messages: {response.status_code}")
                print(f"   Response: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error connecting to Bubu Agent: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def send_message(self, message_type: str, message_text: str) -> bool:
        """Send a message immediately."""
        try:
            response = await self.client.post(
                f"{self.base_url}/send-now",
                json={"type": message_type, "message": message_text},
                headers={"Authorization": f"Bearer {self.bearer_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Message sent successfully!")
                print(f"   Provider: {data.get('provider', 'Unknown')}")
                print(f"   Message ID: {data.get('message_id', 'N/A')}")
                return True
            else:
                print(f"❌ Error sending message: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def display_message_options(self, message_type: str, messages: List[Dict[str, Any]]):
        """Display message options in a nice format."""
        print(f"\n{'='*60}")
        print(f"📝 {message_type.upper()} MESSAGE OPTIONS")
        print(f"{'='*60}")
        
        if not messages:
            print("❌ No messages available")
            return
        
        for i, msg in enumerate(messages, 1):
            print(f"\n{i}. {msg.get('text', 'No text available')}")
            print(f"   Length: {len(msg.get('text', ''))} chars")
            
            # Show message type and status
            if msg.get('is_fallback'):
                print(f"   Type: 📋 Fallback Template")
            elif msg.get('is_ai_generated'):
                print(f"   Type: 🤖 AI Generated (with Bollywood quotes & cheesy lines)")
            else:
                print(f"   Type: 📝 Template-based")
            
            # Show status if available
            if msg.get('status'):
                print(f"   Status: {msg.get('status')}")
            
            print(f"   Index: {msg.get('index', 'N/A')}")
    
    def get_user_choice(self, max_options: int) -> int:
        """Get user choice for message selection."""
        while True:
            try:
                choice = input(f"Select a message (1-{max_options}) or 0 to skip: ").strip()
                choice_num = int(choice)
                
                if choice_num == 0:
                    return 0
                elif 1 <= choice_num <= max_options:
                    return choice_num
                else:
                    print(f"❌ Please enter a number between 0 and {max_options}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    async def run_interactive_session(self):
        """Run the main interactive session."""
        print("🤖 BUBU AGENT - INTERACTIVE MESSAGE SENDER")
        print("=" * 50)
        print(f"🌐 Connecting to: {self.base_url}")
        print(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Check if server is running
        try:
            health_response = await self.client.get(f"{self.base_url}/healthz")
            if health_response.status_code != 200:
                print(f"❌ Bubu Agent health check failed: {health_response.status_code}")
                print(f"   Response: {health_response.text}")
                return
            print("✅ Connected to Bubu Agent successfully!")
        except Exception as e:
            print(f"❌ Cannot connect to Bubu Agent: {e}")
            print("   Make sure the server is running with: uvicorn setup.app:app --host 0.0.0.0 --port 8000")
            import traceback
            traceback.print_exc()
            return
        
        # Ask user if they want to use AI generation
        print("\n🤖 MESSAGE GENERATION OPTIONS")
        print("=" * 40)
        print("1. 📋 Fallback Templates (Fast, reliable)")
        print("2. 🧠 AI Generated (Slower, creative, requires valid HF API key)")
        
        while True:
            try:
                choice = input("Choose generation method (1 or 2): ").strip()
                if choice == "1":
                    use_ai_generation = False
                    print("✅ Using fallback templates")
                    break
                elif choice == "2":
                    use_ai_generation = True
                    print("✅ Using AI generation")
                    break
                else:
                    print("❌ Please enter 1 or 2")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return
        
        message_types = ["morning", "flirty", "night"]
        sent_messages = []
        
        for msg_type in message_types:
            print(f"\n{'🔄'*20}")
            print(f"Getting {msg_type} message options...")
            
            messages = await self.get_message_options(msg_type, use_ai_generation)
            
            if not messages:
                print(f"❌ No {msg_type} messages available")
                continue
            
            self.display_message_options(msg_type, messages)
            
            choice = self.get_user_choice(len(messages))
            
            if choice == 0:
                print(f"⏭️  Skipping {msg_type} message")
                continue
            
            selected_message = messages[choice - 1]
            message_text = selected_message.get('text', '')
            
            print(f"\n📤 Sending {msg_type} message:")
            print(f"   {message_text}")
            
            confirm = input("\nSend this message? (y/N): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                success = await self.send_message(msg_type, message_text)
                if success:
                    sent_messages.append({
                        'type': msg_type,
                        'text': message_text,
                        'timestamp': datetime.now().isoformat()
                    })
            else:
                print(f"❌ {msg_type} message cancelled")
        
        # Summary
        print(f"\n{'📊'*20}")
        print("SESSION SUMMARY")
        print(f"{'📊'*20}")
        
        if sent_messages:
            print(f"✅ Successfully sent {len(sent_messages)} messages:")
            for msg in sent_messages:
                print(f"   • {msg['type'].title()}: {msg['text'][:50]}...")
        else:
            print("ℹ️  No messages were sent")
        
        print(f"\n🎉 Interactive session completed!")

async def main():
    """Main entry point."""
    print("🚀 Starting Bubu Agent Interactive Sender...")
    
    async with InteractiveSender() as sender:
        await sender.run_interactive_session()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
