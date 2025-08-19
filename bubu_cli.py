#!/usr/bin/env python3
"""
Bubu Agent CLI - A romantic command-line interface for sending personalized WhatsApp messages.

Just like in those beautiful Bollywood movies where love finds a way,
this CLI tool helps you express your feelings through automated messages! 💕
"""

import asyncio
import sys
from datetime import date, datetime
from typing import Optional, Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align

from utils import (
    config,
    MessageScheduler,
    get_logger,
    setup_logging
)
from utils.compose_refactored import create_message_composer_refactored
from utils.types import MessageType
from utils.llm_factory import create_llm

# Setup logging
setup_logging(config.settings.log_level)
logger = get_logger(__name__)

# Rich console for beautiful output
console = Console()


def print_banner():
    """Print a beautiful banner for the CLI."""
    banner_text = Text()
    banner_text.append("💕 ", style="bold red")
    banner_text.append("BUBU AGENT CLI", style="bold magenta")
    banner_text.append(" 💕", style="bold red")
    
    subtitle = Text("Your Personal Love Assistant", style="italic cyan")
    
    panel = Panel(
        Align.center(banner_text),
        subtitle=subtitle,
        border_style="magenta",
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print()


def print_romantic_quote():
    """Print a random romantic quote."""
    quotes = [
        "💖 'Dil ko jo baat lagti hai, wahi baat karte hain...' 💖",
        "🌹 'Main tumhare liye sab kuch kar sakta hun...' 🌹",
        "💕 'Tumhare liye main chaand bhi tod launga...' 💕",
        "✨ 'Tumhare liye main taare gin sakta hun...' ✨",
        "💝 'Tumhare liye main kuch bhi kar sakta hun...' 💝"
    ]
    
    import random
    quote = random.choice(quotes)
    console.print(Panel(quote, border_style="magenta", padding=(0, 1)))


class BubuCLI:
    """Main CLI class for Bubu Agent."""
    
    def __init__(self):
        """Initialize the CLI with scheduler and composer."""
        self.scheduler = MessageScheduler()
        self.llm = create_llm()
        self.composer = create_message_composer_refactored(self.llm, self.scheduler.storage)
    
    def show_status(self):
        """Show the current status of the agent."""
        console.print("\n[bold cyan]📊 Current Status:[/bold cyan]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        # Check messenger availability
        try:
            messenger_available = asyncio.run(self.scheduler.messenger.is_available())
            status = "🟢 Healthy" if messenger_available else "🟡 Degraded"
        except Exception:
            status = "🔴 Unhealthy"
        
        table.add_row("Status", status)
        table.add_row("Enabled", "✅ Yes" if config.settings.enabled else "❌ No")
        table.add_row("Provider", config.settings.whatsapp_provider.upper())
        table.add_row("Girlfriend", config.settings.gf_name)
        table.add_row("Timezone", config.settings.timezone)
        table.add_row("Flirty Tone", config.settings.daily_flirty_tone)
        
        console.print(table)
    
    def show_todays_plan(self):
        """Show today's planned message times."""
        console.print("\n[bold cyan]📅 Today's Message Plan:[/bold cyan]")
        
        plan = self.scheduler.get_todays_plan()
        today = date.today()
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Message Type", style="cyan")
        table.add_column("Scheduled Time", style="green")
        table.add_column("Status", style="yellow")
        
        for message_type in ["morning", "flirty", "night"]:
            time_str = plan.get(message_type, "Not scheduled")
            sent = self.scheduler.storage.is_message_sent(today, message_type)
            status = "✅ Sent" if sent else "⏳ Pending"
            
            table.add_row(
                message_type.title(),
                time_str,
                status
            )
        
        console.print(table)
    
    async def preview_messages(self, message_type: str, count: int = 1):
        """Preview messages without sending."""
        console.print(f"\n[bold cyan]👀 Previewing {message_type} messages:[/bold cyan]")
        
        try:
            message_type_enum = MessageType(message_type)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Generating messages...", total=count)
                
                for i in range(count):
                    message = self.composer.get_message_preview(message_type_enum, {
                        "randomize": True,
                        "seed": i
                    })
                    
                    panel = Panel(
                        message,
                        title=f"Message {i+1}",
                        border_style="green",
                        padding=(1, 2)
                    )
                    console.print(panel)
                    
                    progress.update(task, advance=1)
                    
        except Exception as e:
            console.print(f"[red]Error generating preview: {e}[/red]")
    
    async def send_message_now(self, message_type: str, custom_message: Optional[str] = None):
        """Send a message immediately."""
        console.print(f"\n[bold cyan]💌 Sending {message_type} message...[/bold cyan]")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Sending message...", total=1)
                
                if custom_message:
                    success, result_message, provider_info = await self.scheduler.send_custom_message(
                        message_type, custom_message
                    )
                else:
                    success, result_message, provider_info = await self.scheduler.send_message_now_with_info(message_type)
                
                progress.update(task, advance=1)
                
                if success:
                    console.print(f"[green]✅ {result_message}[/green]")
                    if provider_info.get("provider"):
                        console.print(f"[blue]Provider: {provider_info['provider']}[/blue]")
                    if provider_info.get("message_id"):
                        console.print(f"[blue]Message ID: {provider_info['message_id']}[/blue]")
                else:
                    console.print(f"[red]❌ {result_message}[/red]")
                    
        except Exception as e:
            console.print(f"[red]Error sending message: {e}[/red]")
    
    async def dry_run(self):
        """Show what messages would be sent today without actually sending."""
        console.print("\n[bold cyan]🧪 Dry Run - Today's Messages:[/bold cyan]")
        
        try:
            today = date.today()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Generating messages...", total=3)
                
                for message_type_str in ["morning", "flirty", "night"]:
                    message_type = MessageType(message_type_str)
                    result = await self.composer.compose_message(message_type, today)
                    
                    status_emoji = {
                        "already_sent": "✅",
                        "ai_generated": "🤖",
                        "fallback": "📝",
                        "error_fallback": "⚠️"
                    }.get(result.status.value, "❓")
                    
                    panel = Panel(
                        result.text if result.text else "[No message]",
                        title=f"{status_emoji} {message_type_str.title()} ({result.status.value})",
                        border_style="blue",
                        padding=(1, 2)
                    )
                    console.print(panel)
                    
                    progress.update(task, advance=1)
                    
        except Exception as e:
            console.print(f"[red]Error in dry run: {e}[/red]")
    
    def show_recent_messages(self, days: int = 7):
        """Show recent messages from storage."""
        console.print(f"\n[bold cyan]📚 Recent Messages (Last {days} days):[/bold cyan]")
        
        try:
            messages = self.scheduler.storage.get_recent_messages(days)
            
            if not messages:
                console.print("[yellow]No recent messages found.[/yellow]")
                return
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Date", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Message", style="white")
            
            for msg in messages:
                table.add_row(
                    msg.date,
                    msg.slot.title(),
                    msg.status,
                    msg.text[:50] + "..." if len(msg.text) > 50 else msg.text
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error fetching recent messages: {e}[/red]")
    
    def interactive_mode(self):
        """Start interactive mode for the CLI."""
        console.print("\n[bold magenta]🎭 Welcome to Interactive Mode![/bold magenta]")
        console.print("Let's make some magic happen! ✨\n")
        
        while True:
            console.print("\n[bold cyan]What would you like to do?[/bold cyan]")
            console.print("1. 📊 Show Status")
            console.print("2. 📅 Show Today's Plan")
            console.print("3. 👀 Preview Messages")
            console.print("4. 💌 Send Message Now")
            console.print("5. 🧪 Dry Run")
            console.print("6. 📚 Show Recent Messages")
            console.print("7. 💕 Show Romantic Quote")
            console.print("8. 🚪 Exit")
            
            choice = Prompt.ask("\nEnter your choice", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
            
            if choice == "1":
                self.show_status()
            elif choice == "2":
                self.show_todays_plan()
            elif choice == "3":
                message_type = Prompt.ask("Message type", choices=["morning", "flirty", "night"])
                count = int(Prompt.ask("Number of previews", default="1"))
                asyncio.run(self.preview_messages(message_type, count))
            elif choice == "4":
                message_type = Prompt.ask("Message type", choices=["morning", "flirty", "night"])
                custom = Prompt.ask("Custom message (press Enter to generate)", default="")
                custom = custom if custom.strip() else None
                asyncio.run(self.send_message_now(message_type, custom))
            elif choice == "5":
                asyncio.run(self.dry_run())
            elif choice == "6":
                days = int(Prompt.ask("Number of days", default="7"))
                self.show_recent_messages(days)
            elif choice == "7":
                print_romantic_quote()
            elif choice == "8":
                console.print("\n[bold green]💕 Thank you for using Bubu Agent CLI![/bold green]")
                console.print("May your love story be as beautiful as a Bollywood movie! 🌹")
                break


@click.group()
@click.version_option(version="1.0.0", prog_name="Bubu Agent CLI")
def cli():
    """Bubu Agent CLI - Your Personal Love Assistant 💕
    
    Just like in those beautiful Bollywood movies where love finds a way,
    this CLI tool helps you express your feelings through automated messages!
    """
    pass


@cli.command()
def status():
    """Show the current status of the agent."""
    print_banner()
    bubu = BubuCLI()
    bubu.show_status()


@cli.command()
def plan():
    """Show today's planned message times."""
    print_banner()
    bubu = BubuCLI()
    bubu.show_todays_plan()


@cli.command()
@click.option("--type", "-t", "message_type", 
              type=click.Choice(["morning", "flirty", "night"]),
              required=True, help="Type of message to preview")
@click.option("--count", "-c", default=1, help="Number of previews to generate")
def preview(message_type, count):
    """Preview messages without sending."""
    print_banner()
    bubu = BubuCLI()
    asyncio.run(bubu.preview_messages(message_type, count))


@cli.command()
@click.option("--type", "-t", "message_type", 
              type=click.Choice(["morning", "flirty", "night"]),
              required=True, help="Type of message to send")
@click.option("--message", "-m", help="Custom message to send (optional)")
def send(message_type, message):
    """Send a message immediately."""
    print_banner()
    bubu = BubuCLI()
    asyncio.run(bubu.send_message_now(message_type, message))


@cli.command()
def dry_run():
    """Show what messages would be sent today without actually sending."""
    print_banner()
    bubu = BubuCLI()
    asyncio.run(bubu.dry_run())


@cli.command()
@click.option("--days", "-d", default=7, help="Number of days to look back")
def recent(days):
    """Show recent messages from storage."""
    print_banner()
    bubu = BubuCLI()
    bubu.show_recent_messages(days)


@cli.command()
def interactive():
    """Start interactive mode for a beautiful CLI experience."""
    print_banner()
    print_romantic_quote()
    bubu = BubuCLI()
    bubu.interactive_mode()


@cli.command()
def quote():
    """Show a random romantic quote."""
    print_banner()
    print_romantic_quote()


if __name__ == "__main__":
    cli()
