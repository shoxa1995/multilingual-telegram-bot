#!/bin/bash
# Workflow-compatible Telegram bot runner for Replit
# This script starts the Telegram bot using the workflow mechanism

echo "Starting Telegram bot as a persistent workflow..."

# Make the Python script executable
chmod +x telegram_bot_workflow.py

# Start the bot directly, the workflow will handle restarting if needed
python telegram_bot_workflow.py