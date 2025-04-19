# Telegram Bot Deployment Guide

This guide provides instructions for deploying your Telegram Bot on a MacBook or Linux server.

## Option 1: MacBook Deployment

### Prerequisites
1. Python 3.10 or newer
2. Terminal access
3. Your Telegram Bot token from BotFather

### Setup Steps

1. **Unzip the deployment package**
   ```bash
   unzip deployment_package.zip
   cd deployment_package
   ```

2. **Run the setup script**
   ```bash
   ./setup.sh
   ```
   This will:
   - Create a Python virtual environment
   - Install all required dependencies
   - Create a template .env file

3. **Configure your bot**
   Edit the .env file with your editor of choice:
   ```bash
   nano .env
   ```
   Replace the placeholder with your actual bot token:
   ```
   BOT_TOKEN=your_actual_bot_token_here
   ```

4. **Run the bot**
   ```bash
   ./run_bot.sh
   ```

5. **To keep the bot running when you close Terminal**
   Use `nohup` to run the bot in the background:
   ```bash
   nohup ./run_bot.sh > bot_output.log 2>&1 &
   ```
   This will keep the bot running even when you close the terminal window.

6. **To check if the bot is running**
   ```bash
   ps aux | grep python
   ```

7. **To stop the bot**
   ```bash
   pkill -f ultra_simple_bot.py
   ```

## Option 2: Linux Server Deployment

### Prerequisites
1. A Linux server (Ubuntu, Debian, CentOS, etc.)
2. SSH access to the server
3. Python 3.10 or newer installed on the server

### Setup Steps

1. **Upload the deployment package to your server**
   ```bash
   scp deployment_package.zip user@your-server:~/
   ```

2. **SSH into your server**
   ```bash
   ssh user@your-server
   ```

3. **Unzip and set up the bot**
   ```bash
   unzip deployment_package.zip
   cd deployment_package
   ./setup.sh
   ```

4. **Configure your bot**
   ```bash
   nano .env
   ```
   Add your bot token:
   ```
   BOT_TOKEN=your_actual_bot_token_here
   ```

5. **Create a systemd service for reliable operation**
   Create a service file:
   ```bash
   sudo nano /etc/systemd/system/telegram-bot.service
   ```

   Add the following content (adjust paths as needed):
   ```
   [Unit]
   Description=Telegram Booking Bot
   After=network.target

   [Service]
   User=your_username
   WorkingDirectory=/home/your_username/deployment_package
   ExecStart=/home/your_username/deployment_package/venv/bin/python /home/your_username/deployment_package/persistent_bot.py
   Restart=always
   RestartSec=5
   StandardOutput=syslog
   StandardError=syslog
   SyslogIdentifier=telegram-bot
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   ```

6. **Enable and start the service**
   ```bash
   sudo systemctl enable telegram-bot.service
   sudo systemctl start telegram-bot.service
   ```

7. **Check the status**
   ```bash
   sudo systemctl status telegram-bot.service
   ```

8. **View logs**
   ```bash
   sudo journalctl -u telegram-bot.service
   ```

## Troubleshooting

### Bot not responding
1. Check if the bot process is running:
   ```bash
   ps aux | grep python
   ```

2. Check the bot logs:
   ```bash
   cat persistent_bot.log
   ```

3. Verify your bot token is correct:
   - Test it with curl:
     ```bash
     curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
     ```
   - You should get a JSON response with your bot's details

4. Check firewall settings:
   - Your server must be able to make outbound HTTPS connections to api.telegram.org

### Can't install dependencies
1. Make sure Python development tools are installed:
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-dev python3-pip python3-venv
   
   # CentOS/RHEL
   sudo yum install python3-devel python3-pip
   ```

2. For PostgreSQL dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt install libpq-dev
   
   # CentOS/RHEL
   sudo yum install postgresql-devel
   ```

## Extending the Bot

The package includes three different bot implementations:

1. **ultra_simple_bot.py** - Basic implementation for quick start
2. **direct_telegram_bot.py** - Implementation with language selection
3. **persistent_bot.py** - Implementation with auto-restart capability

To add more features, modify these files according to your needs.