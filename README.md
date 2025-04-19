# Telegram Booking Bot

A multilingual Telegram bot for appointment booking.

## Setup Instructions

1. Install Python 3.10 or newer
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your Telegram Bot Token
4. Run the bot: `python ultra_simple_bot.py`

## Available Bot Implementations

- `ultra_simple_bot.py` - The simplest implementation for quick start
- `direct_telegram_bot.py` - Implementation with language selection
- `persistent_bot.py` - Implementation with auto-restart capability

## Running as a Service

To run the bot as a service on Linux, create a systemd service file:

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Add the following content:

```
[Unit]
Description=Telegram Booking Bot
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/bot/directory
ExecStart=/usr/bin/python3 /path/to/bot/directory/persistent_bot.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=telegram-bot
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable telegram-bot.service
sudo systemctl start telegram-bot.service
```
