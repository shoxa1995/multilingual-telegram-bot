#!/bin/bash
# Script to run the direct Telegram bot

# First, stop any existing bots
echo "Stopping any running bot processes..."
pkill -f "direct_telegram_bot.py" || echo "No direct_telegram_bot.py process found"
pkill -f "telegram_bot_workflow.py" || echo "No telegram_bot_workflow.py process found"
pkill -f "persistent_bot.py" || echo "No persistent_bot.py process found"
pkill -f "ultra_simple_bot.py" || echo "No ultra_simple_bot.py process found"
sleep 2

# Make the script executable
chmod +x direct_telegram_bot.py

# Start the bot in the background
echo "Starting direct Telegram bot..."
nohup python direct_telegram_bot.py > direct_bot_output.log 2>&1 &
BOT_PID=$!
echo "Started bot with PID $BOT_PID"

# Save PID for future use
echo $BOT_PID > direct_bot.pid

echo "Direct Telegram bot is now running"
echo "You can message @gsbookingbot on Telegram"
echo "To stop the bot: kill \$(cat direct_bot.pid)"
echo "To restart the bot: ./run_direct_bot.sh"