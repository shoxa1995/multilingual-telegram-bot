#!/bin/bash
# Script to run the persistent Telegram bot

# First, stop any existing bots
echo "Stopping any running bot processes..."
pkill -f "direct_telegram_bot.py" || echo "No direct_telegram_bot.py process found"
pkill -f "telegram_bot_workflow.py" || echo "No telegram_bot_workflow.py process found"
pkill -f "persistent_bot.py" || echo "No persistent_bot.py process found"
pkill -f "ultra_simple_bot.py" || echo "No ultra_simple_bot.py process found"
sleep 2

# Make the script executable
chmod +x persistent_bot.py

# Make BOT_TOKEN available in environment
export BOT_TOKEN=$(grep BOT_TOKEN .replit.secrets | cut -d= -f2) || echo "No BOT_TOKEN found"

# Start the bot in the background
echo "Starting persistent Telegram bot with direct access to BOT_TOKEN..."
nohup python persistent_bot.py > persistent_bot_direct.log 2>&1 &
BOT_PID=$!
echo "Started bot with PID $BOT_PID"

# Save PID for future use
echo $BOT_PID > persistent_bot.pid

echo "Persistent Telegram bot is now running"
echo "You can message @gsbookingbot on Telegram"
echo "To stop the bot: kill \$(cat persistent_bot.pid)"
echo "To restart the bot: ./run_persistent_bot.sh"

# Monitor the bot output for a few seconds
echo -e "\nChecking initial bot output:"
sleep 5
tail -20 persistent_bot.log