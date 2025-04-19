#!/bin/bash
# Script to run the Telegram bot in the background

# First, stop any running bots
echo "Stopping any running bot processes..."
pkill -f "ultra_simple_bot.py" || echo "No ultra_simple_bot.py process found"
pkill -f "working_telegram_bot.py" || echo "No working_telegram_bot.py process found"
sleep 2

# Start the ultra simple bot
echo "Starting Telegram bot..."
python ultra_simple_bot.py > ultra_simple_output.log 2>&1 &
BOT_PID=$!
echo "Started bot with PID $BOT_PID"

# Save PID for future reference
echo $BOT_PID > telegram_bot.pid

echo "Telegram bot is now running"
echo "Try messaging @gsbookingbot on Telegram"
echo "The bot supports these commands:"
echo "  /start - Start the bot"
echo "  /help - Show help"
echo "  /test - Test if the bot is responding"
echo ""
echo "To stop the bot: kill \$(cat telegram_bot.pid)"
echo "To restart: ./run_telegram_bot.sh"