#!/bin/bash
# Restart the Telegram bot

echo "Stopping any running Telegram bot processes..."
pkill -f "working_telegram_bot.py" || echo "No working_telegram_bot.py process found"
pkill -f "run_bot_standalone.py" || echo "No run_bot_standalone.py process found"
sleep 2

echo "Starting Telegram bot..."
python working_telegram_bot.py > bot_working_output.log 2>&1 &
echo "Started bot with PID $!"

echo "Telegram bot restarted successfully"