#!/bin/bash
# Script to run the persistent Telegram bot

# First, stop any running bots
echo "Stopping any running bot processes..."
pkill -f "persistent_bot.py" || echo "No persistent_bot.py process found"
pkill -f "ultra_simple_bot.py" || echo "No ultra_simple_bot.py process found"
sleep 2

# Start the persistent bot
echo "Starting persistent Telegram bot..."
nohup python persistent_bot.py > persistent_bot_output.log 2>&1 &
BOT_PID=$!
echo "Started persistent bot with PID $BOT_PID"

# Create a heartbeat monitor in the background
cat > bot_monitor.sh << 'MONITOR'
#!/bin/bash
# Bot heartbeat monitor - restarts the bot if it dies

while true; do
  if [ -f "bot_running.pid" ]; then
    PID=$(cat bot_running.pid)
    if ! ps -p $PID > /dev/null; then
      echo "$(date) - Bot process died, restarting..." >> bot_monitor.log
      ./run_persistent_bot.sh
      sleep 10
    fi
  else
    echo "$(date) - PID file not found, starting bot..." >> bot_monitor.log
    ./run_persistent_bot.sh
    sleep 10
  fi
  sleep 30
done
MONITOR

chmod +x bot_monitor.sh

# Start the monitor
nohup ./bot_monitor.sh > bot_monitor_output.log 2>&1 &
MONITOR_PID=$!
echo "Started bot monitor with PID $MONITOR_PID"

echo "Persistent Telegram bot is now running with auto-restart capability"
echo "Try messaging @gsbookingbot on Telegram"
echo "The bot supports these commands:"
echo "  /start - Start the bot"
echo "  /help - Show help"
echo "  /test - Test if the bot is responding"
