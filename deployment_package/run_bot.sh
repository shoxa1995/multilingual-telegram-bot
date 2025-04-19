#!/bin/bash
# Script to run the Telegram bot

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Run the bot
python ultra_simple_bot.py
