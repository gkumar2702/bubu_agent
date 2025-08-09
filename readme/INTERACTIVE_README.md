# Interactive Message Sender

## Overview

The `interactive_sender.py` script provides an interactive command-line interface to preview and send WhatsApp messages through your Bubu Agent. It allows you to:

- View 5 different message options for each type (morning, flirty, night)
- See both AI-generated and fallback template messages
- Select and send messages immediately
- Preview messages before sending

## Features

### 🎯 **Message Types**
- **Morning**: Sweet and motivational messages
- **Flirty**: Playful and respectful messages  
- **Night**: Sweet and calming messages

### 📝 **Message Options**
- **5 AI-generated messages** per type (with randomization)
- **3 fallback templates** per type (marked with 📋)
- **Character count** for each message
- **Fallback indicator** for template messages

### 🔧 **Interactive Features**
- **Message selection**: Choose from numbered options
- **Skip option**: Press 0 to skip any message type
- **Confirmation**: Confirm before sending each message
- **Session summary**: See all sent messages at the end

## Usage

### Prerequisites

1. **Bubu Agent running**: Make sure your Bubu Agent is running:
   ```bash
   uvicorn setup.app:app --host 0.0.0.0 --port 8000
   ```

2. **Environment configured**: Ensure your `.env` file has the correct settings:
   ```bash
   API_BEARER_TOKEN=your_secure_bearer_token_here
   GF_NAME=YourGirlfriendName
   # ... other settings
   ```

### Running the Interactive Sender

```bash
python interactive_sender.py
```

### Example Session

```
🤖 BUBU AGENT - INTERACTIVE MESSAGE SENDER
==================================================
🌐 Connecting to: http://localhost:8000
⏰ Current time: 2025-08-09 16:25:42

✅ Connected to Bubu Agent successfully!

============================================================
📝 MORNING MESSAGE OPTIONS
============================================================

1. Good morning YourGirlfriendName! 🌞 You're capable of amazing things today. — bubu 💕
   Length: 83 chars

2. Good morning YourGirlfriendName! 🌞 Here's to a day full of possibilities and smiles. — with love, bubu
   Length: 102 chars

Select a message (1-8) or 0 to skip: 1

📤 Sending morning message:
   Good morning YourGirlfriendName! 🌞 You're capable of amazing things today. — bubu 💕

Send this message? (y/N): y
✅ Message sent successfully!
   Provider: twilio
   Message ID: None
```

## Configuration

### Customizing Message Options

You can modify the script to change:
- **Number of options**: Edit the `count` parameter in the request
- **Include fallbacks**: Set `include_fallback` to `True`/`False`
- **Randomization**: Set `randomize` to `True`/`False`

### Server URL

By default, the script connects to `http://localhost:8000`. To change this:

```python
async with InteractiveSender(base_url="http://your-server:8000") as sender:
    await sender.run_interactive_session()
```

## Troubleshooting

### Connection Issues
```
❌ Cannot connect to Bubu Agent: All connection attempts failed
```
**Solution**: Make sure the Bubu Agent server is running on port 8000.

### Authentication Issues
```
❌ Error getting messages: 401
```
**Solution**: Check that your `API_BEARER_TOKEN` in `.env` matches the one expected by the server.

### Message Sending Issues
```
❌ Error sending message: 422
```
**Solution**: This usually means the message format is incorrect. The script should handle this automatically.

## Tips

1. **Preview First**: Use the interactive sender to preview messages before setting up automatic scheduling
2. **Test Different Types**: Try all three message types to see the variety
3. **Check Fallbacks**: Fallback templates (marked with 📋) are useful when AI generation fails
4. **Skip When Needed**: Press 0 to skip any message type you don't want to send

## Security Notes

- The script uses the `API_BEARER_TOKEN` from your `.env` file
- Messages are sent to the configured `GF_WHATSAPP_NUMBER`
- All API calls are authenticated and logged
- The script doesn't store any sensitive data locally

## Integration

The interactive sender works with all Bubu Agent features:
- ✅ **WhatsApp Integration**: Works with Twilio and Meta providers
- ✅ **Message Storage**: Sent messages are recorded in the database
- ✅ **Idempotency**: Prevents duplicate sends for the same day/slot
- ✅ **Logging**: All activities are logged with structured logging

---

**Happy messaging! 💕**
