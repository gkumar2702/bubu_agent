# 💕 Bubu Agent CLI

A beautiful command-line interface for your personal love assistant! Just like in those romantic Bollywood movies where love finds a way, this CLI tool helps you express your feelings through automated WhatsApp messages.

## 🌟 Features

- **Beautiful Interface**: Rich, colorful CLI with emojis and romantic styling
- **Interactive Mode**: Menu-driven interface for easy navigation
- **Message Preview**: See what messages will be sent before sending
- **Dry Run**: Test message generation without actually sending
- **Status Monitoring**: Check your agent's health and configuration
- **Message History**: View recent messages from storage
- **Romantic Quotes**: Get inspired with beautiful Bollywood quotes

## 🚀 Quick Start

### Installation

1. Make sure you have the required dependencies:
```bash
pip install click rich
```

2. Make the CLI executable:
```bash
chmod +x bubu_cli.py
```

### Basic Usage

```bash
# Show help
python bubu_cli.py --help

# Check status
python bubu_cli.py status

# Show today's plan
python bubu_cli.py plan

# Preview messages
python bubu_cli.py preview --type morning --count 3

# Dry run (see what would be sent)
python bubu_cli.py dry-run

# Send a message immediately
python bubu_cli.py send --type flirty

# Send a custom message
python bubu_cli.py send --type morning --message "Good morning my love! 💕"

# Show recent messages
python bubu_cli.py recent --days 7

# Get a romantic quote
python bubu_cli.py quote

# Start interactive mode
python bubu_cli.py interactive
```

## 🎭 Interactive Mode

The interactive mode provides a beautiful menu-driven interface:

```bash
python bubu_cli.py interactive
```

This will show you a menu with options:
1. 📊 Show Status
2. 📅 Show Today's Plan
3. 👀 Preview Messages
4. 💌 Send Message Now
5. 🧪 Dry Run
6. 📚 Show Recent Messages
7. 💕 Show Romantic Quote
8. 🚪 Exit

## 📋 Commands Reference

### `status`
Shows the current status of your Bubu Agent including:
- Health status (Healthy/Degraded/Unhealthy)
- Configuration details
- WhatsApp provider status
- Girlfriend name and settings

### `plan`
Displays today's scheduled message times and their current status (Sent/Pending).

### `preview --type <type> [--count <number>]`
Preview messages without sending them.
- `--type`: Message type (morning/flirty/night)
- `--count`: Number of previews to generate (default: 1)

### `send --type <type> [--message <text>]`
Send a message immediately.
- `--type`: Message type (morning/flirty/night)
- `--message`: Custom message (optional, will generate if not provided)

### `dry-run`
Show what messages would be sent today without actually sending them.

### `recent [--days <number>]`
Show recent messages from storage.
- `--days`: Number of days to look back (default: 7)

### `quote`
Display a random romantic Bollywood quote.

### `interactive`
Start the beautiful interactive mode with menu navigation.

## 🎨 Beautiful Output

The CLI uses the Rich library to provide:
- Colorful tables and panels
- Progress bars with spinners
- Beautiful formatting and styling
- Emoji support
- Romantic quotes and messages

## 💝 Romantic Features

- **Bollywood Quotes**: Random romantic quotes from famous movies
- **Love-themed Styling**: Pink and magenta colors, heart emojis
- **Personalized Messages**: Uses your girlfriend's name from configuration
- **Beautiful Banners**: Eye-catching startup banners

## 🔧 Configuration

The CLI uses the same `.env` configuration as the web application:
- WhatsApp provider settings
- Girlfriend's name and number
- Hugging Face API credentials
- Timezone and scheduling preferences

## 🎯 Example Session

```bash
$ python bubu_cli.py interactive

╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                            💕 BUBU AGENT CLI 💕                                             │
╰─────────────────────────────────────── Your Personal Love Assistant ────────────────────────────────────────╯

╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ 💖 'Dil ko jo baat lagti hai, wahi baat karte hain...' 💖                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

🎭 Welcome to Interactive Mode!
Let's make some magic happen! ✨

What would you like to do?
1. 📊 Show Status
2. 📅 Show Today's Plan
3. 👀 Preview Messages
4. 💌 Send Message Now
5. 🧪 Dry Run
6. 📚 Show Recent Messages
7. 💕 Show Romantic Quote
8. 🚪 Exit

Enter your choice: 3
Message type: morning
Number of previews: 2

👀 Previewing morning messages:
╭───────────────────────────────────────────────── Message 1 ─────────────────────────────────────────────────╮
│ Good morning Preeti Bubu! 🌞 You're capable of amazing things today, and I can't wait to see all the       │
│ wonderful ways you'll make the world a better place. Your kindness knows no bounds! — missing you, bubu    │
│ gourav                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 🌹 Why CLI?

Just like in those beautiful Bollywood movies where the hero chooses the perfect way to express his love, the CLI provides:

- **Personal Touch**: Direct interaction with your love assistant
- **Quick Access**: No need to open a browser or remember URLs
- **Beautiful Experience**: Rich, colorful interface that's a joy to use
- **Romantic Feel**: Every interaction feels special and personal
- **Efficiency**: Fast commands for quick actions

## 💕 Love Notes

*"Dil ko jo baat lagti hai, wahi baat karte hain..."* - We speak what touches the heart.

Your Bubu Agent CLI is designed to make every interaction feel special, just like those magical moments in romantic movies where love finds its perfect expression! 💖✨
