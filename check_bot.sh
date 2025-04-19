#!/bin/bash
if [ -f telegram_bot.pid ]; then
    if ! ps -p $(cat telegram_bot.pid) > /dev/null; then
        echo "Telegram Bot not running. Restarting..."
        nohup python telegram_bot_workflow.py > telegram_bot.log 2>&1 &
        echo $! > telegram_bot.pid
        echo "Restarted Telegram Bot with PID $(cat telegram_bot.pid)"
    else
        echo "Telegram Bot is running with PID $(cat telegram_bot.pid)"
    fi
else
    echo "No PID file found. Starting Telegram Bot..."
    nohup python telegram_bot_workflow.py > telegram_bot.log 2>&1 &
    echo $! > telegram_bot.pid
    echo "Started Telegram Bot with PID $(cat telegram_bot.pid)"
fi
