"""Pytest configuration and fixtures for Bubu Agent tests."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest


@pytest.fixture
def fixed_seed_date() -> date:
    """Return a fixed date for deterministic testing."""
    return date(2024, 1, 15)


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Return sample configuration for testing."""
    return {
        "general": {
            "max_message_length": 700,
            "max_emojis": 5,
            "allow_emojis": True,
            "enable_safety_filters": True,
            "enable_content_policy": True,
            "enable_bollywood_quotes": True,
            "enable_cheesy_lines": True
        },
        "tone": {
            "daily_flirty_tone": "romantic",
            "overall_style": "warm",
            "cultural_neutrality": True
        },
        "signature_closers": [
            "— your bubu gourav",
            "— bubu gourav ❤️",
            "— your love",
            "— bubu gourav 💕",
            "— with love, bubu gourav",
            "— forever yours, bubu gourav",
            "— missing you, bubu gourav",
            "— your forever love",
            "— bubu gourav 💖",
            "— your soulmate"
        ],
        "bollywood_quotes": [
            "Tumhare liye main kuch bhi kar sakta hun... bas tum khush raho",
            "Mere liye tum sabse upar ho, sabse aage ho",
            "Tumhari muskaan meri duniya hai",
            "Main tumhare bina jeena nahi chahta",
            "Tum meri zindagi ka sabse khoobsurat hissa ho",
            "Mere liye tum perfect ho",
            "Tumhari aankhon mein meri duniya basi hai",
            "Main tumhare liye chaand bhi tod launga",
            "Tumhari yaad mein main pagal ho jata hun",
            "Mere liye tum sab kuch ho"
        ],
        "cheesy_lines": [
            "You're the WiFi to my heart - I can't connect without you! 📶💕",
            "Are you a parking ticket? Because you've got FINE written all over you! 🚗💖",
            "Are you a magician? Because whenever I look at you, everyone else disappears! ✨👀",
            "Do you have a map? I keep getting lost in your eyes! 🗺️👁️",
            "Are you made of copper and tellurium? Because you're Cu-Te! 🧪💕",
            "Do you like science? Because we have chemistry! 🔬💕",
            "Are you a camera? Because every time I look at you, I smile! 📸😊",
            "Do you have a Band-Aid? Because I just scraped my knee falling for you! 🩹💕",
            "Are you a time traveler? Because I can see you in my future! ⏰🔮",
            "Do you like camping? Because I'd love to pitch a tent with you! ⛺💕"
        ],
        "fallback_templates": {
            "morning": [
                "Good morning {GF_NAME}! 🌅 Wishing you a beautiful day filled with joy, success, and endless possibilities. Remember, you have the power to make today amazing - your smile alone can brighten someone's entire day! {closer}",
                "Morning {GF_NAME}! ☀️ May your day be as wonderful and extraordinary as you are. You're not just starting a new day, you're creating a new chapter in your beautiful story. Let's make it count! {closer}",
                "Good morning {GF_NAME}! 🌞 Here's to a day full of possibilities, smiles, and moments that take your breath away. You're the kind of person who makes ordinary days feel magical. {closer}",
                "Rise and shine {GF_NAME}! ✨ You've got this day in the bag, and I know you'll handle everything with the grace and strength that makes you so special. Your determination is truly inspiring! {closer}",
                "Good morning {GF_NAME}! 🌅 Your positive energy will light up the world today, just like you light up my world every single day. You're a force of nature, beautiful and unstoppable! {closer}"
            ],
            "flirty": [
                "Hey {GF_NAME}! 😊 Just thinking about your beautiful smile and how it brightens my day. You're like sunshine on a cloudy day - impossible to ignore and absolutely mesmerizing! {closer}",
                "Hi {GF_NAME}! 💕 Your laugh is absolutely contagious - I can't help but smile thinking about it. It's the kind of sound that makes my heart skip a beat and my world feel complete! {closer}",
                "Hey there {GF_NAME}! 😍 You're the highlight of my day, every day. Just the thought of you makes my heart race and my day instantly better. You're my favorite person in the whole world! {closer}",
                "Hi {GF_NAME}! 💖 Just wanted to remind you how amazing you are. You're not just beautiful, you're absolutely breathtaking - inside and out. You make my world complete! {closer}",
                "Hey {GF_NAME}! 😊 Your positive energy is absolutely magnetic. I'm drawn to you like a moth to a flame, and I never want to be anywhere else. You're my everything! {closer}"
            ],
            "night": [
                "Good night {GF_NAME}! 🌙 Thank you for being the amazing person you are. Sweet dreams filled with love, joy, and all the beautiful things you deserve. You make my world complete! {closer}",
                "Night {GF_NAME}! 🌟 Rest well knowing you're loved and appreciated beyond measure. Your presence in my life is the greatest gift I've ever received. Sleep peacefully, my love! {closer}",
                "Good night {GF_NAME}! 🌙 May your dreams be as beautiful and extraordinary as you are. You deserve all the happiness, love, and wonderful things that life has to offer. Sweet dreams! {closer}",
                "Sweet dreams {GF_NAME}! 🌟 Thank you for another wonderful day filled with your love and laughter. You're the reason my life feels complete and my heart feels full. Rest well, beautiful! {closer}",
                "Good night {GF_NAME}! 🌙 You deserve all the peaceful rest in the world, and so much more. Your kindness, love, and beautiful spirit make every day worth living. Sleep tight, my everything! {closer}"
            ]
        },
        "prompt_templates": {
            "morning": {
                "system": "You are a loving partner sending a good morning message. Be warm, sweet, and include a motivational line. Keep it under 700 characters. Use 2-4 emojis. Personalize with {GF_NAME}. Feel free to include Bollywood-style romantic expressions or cheesy lines for fun. Be culturally inclusive and make it memorable.",
                "user": "Create a good morning message for {GF_NAME}. Include: - A sweet and engaging greeting - A motivational line that inspires - A romantic or cheesy element (optional) - A warm and loving sign-off Make it personal, uplifting, and memorable. Feel free to be romantic and cheesy!"
            },
            "flirty": {
                "system": "You are a loving partner sending a playful, flirty message. Be respectful and fun. Keep it under 700 characters. Use 2-4 emojis. Personalize with {GF_NAME}. Tone: {DAILY_FLIRTY_TONE}. Feel free to include Bollywood-style romantic expressions or cheesy pickup lines. Be culturally inclusive and make it memorable.",
                "user": "Create a {DAILY_FLIRTY_TONE} flirty message for {GF_NAME}. Include: - A playful and engaging hook - A unique personal compliment - A romantic or cheesy element (optional) - A short imaginative scenario Make it fun, respectful, and memorable. Feel free to be romantic and cheesy!"
            },
            "night": {
                "system": "You are a loving partner sending a good night message. Be gentle, calming, and appreciative. Keep it under 700 characters. Use 2-4 emojis. Personalize with {GF_NAME}. Feel free to include Bollywood-style romantic expressions or cheesy lines for fun. Be culturally inclusive and make it memorable.",
                "user": "Create a good night message for {GF_NAME}. Include: - A gentle and loving wrap-up - An appreciation line - A romantic or cheesy element (optional) - A calm and soothing wish Make it soothing, loving, and memorable. Feel free to be romantic and cheesy!"
            }
        },
        "huggingface": {
            "max_new_tokens": 150,
            "temperature": 0.8,
            "top_p": 0.9,
            "do_sample": True,
            "timeout_seconds": 30,
            "max_retries": 3
        }
    }


@pytest.fixture
def test_gf_name() -> str:
    """Return test girlfriend name."""
    return "TestGirlfriend"


@pytest.fixture
def test_daily_flirty_tone() -> str:
    """Return test daily flirty tone."""
    return "romantic"
