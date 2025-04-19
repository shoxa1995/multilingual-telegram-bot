#!/usr/bin/env python3
"""
Package the bot files for deployment outside of Replit.
This script creates a standalone package that can be run on any server
with Python and the required dependencies installed.
"""
import os
import shutil
import sys

def create_deployment_package(target_dir="./deployment_package"):
    """Create a deployment package with all needed files"""
    print(f"Creating deployment package in {target_dir}...")
    
    # Create target directory
    if os.path.exists(target_dir):
        print(f"Target directory {target_dir} already exists. Removing...")
        shutil.rmtree(target_dir)
    
    os.makedirs(target_dir)
    os.makedirs(os.path.join(target_dir, "bot"))
    
    # Core files to include
    core_files = [
        "ultra_simple_bot.py",    # Basic bot implementation
        "direct_telegram_bot.py",  # Direct implementation
        "persistent_bot.py",       # Persistent implementation
        "models.py",               # Database models
        "requirements.txt",        # Dependencies list
        "README.md",               # Instructions
        ".env.example"             # Example environment file
    ]
    
    # Create requirements.txt if it doesn't exist
    if not os.path.exists("requirements.txt"):
        with open("requirements.txt", "w") as f:
            f.write("aiogram>=3.0.0\n")
            f.write("sqlalchemy>=2.0.0\n")
            f.write("psycopg2-binary>=2.9.0\n")
            f.write("python-dotenv>=1.0.0\n")
    
    # Create .env.example if it doesn't exist
    if not os.path.exists(".env.example"):
        with open(".env.example", "w") as f:
            f.write("BOT_TOKEN=your_bot_token_here\n")
            f.write("DATABASE_URL=postgresql://username:password@localhost:5432/dbname\n")
    
    # Create README.md if it doesn't exist
    if not os.path.exists("README.md"):
        with open("README.md", "w") as f:
            f.write("# Telegram Booking Bot\n\n")
            f.write("A multilingual Telegram bot for appointment booking.\n\n")
            f.write("## Setup Instructions\n\n")
            f.write("1. Install Python 3.10 or newer\n")
            f.write("2. Install dependencies: `pip install -r requirements.txt`\n")
            f.write("3. Copy `.env.example` to `.env` and fill in your Telegram Bot Token\n")
            f.write("4. Run the bot: `python ultra_simple_bot.py`\n\n")
            f.write("## Available Bot Implementations\n\n")
            f.write("- `ultra_simple_bot.py` - The simplest implementation for quick start\n")
            f.write("- `direct_telegram_bot.py` - Implementation with language selection\n")
            f.write("- `persistent_bot.py` - Implementation with auto-restart capability\n\n")
            f.write("## Running as a Service\n\n")
            f.write("To run the bot as a service on Linux, create a systemd service file:\n\n")
            f.write("```bash\n")
            f.write("sudo nano /etc/systemd/system/telegram-bot.service\n")
            f.write("```\n\n")
            f.write("Add the following content:\n\n")
            f.write("```\n")
            f.write("[Unit]\n")
            f.write("Description=Telegram Booking Bot\n")
            f.write("After=network.target\n\n")
            f.write("[Service]\n")
            f.write("User=your_username\n")
            f.write("WorkingDirectory=/path/to/bot/directory\n")
            f.write("ExecStart=/usr/bin/python3 /path/to/bot/directory/persistent_bot.py\n")
            f.write("Restart=always\n")
            f.write("RestartSec=5\n")
            f.write("StandardOutput=syslog\n")
            f.write("StandardError=syslog\n")
            f.write("SyslogIdentifier=telegram-bot\n")
            f.write("Environment=PYTHONUNBUFFERED=1\n\n")
            f.write("[Install]\n")
            f.write("WantedBy=multi-user.target\n")
            f.write("```\n\n")
            f.write("Enable and start the service:\n\n")
            f.write("```bash\n")
            f.write("sudo systemctl enable telegram-bot.service\n")
            f.write("sudo systemctl start telegram-bot.service\n")
            f.write("```\n")
    
    # Copy core files
    for file in core_files:
        if os.path.exists(file):
            shutil.copy(file, target_dir)
            print(f"Copied {file}")
        else:
            print(f"Warning: {file} not found, skipping")
    
    # Create a run script
    with open(os.path.join(target_dir, "run_bot.sh"), "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# Script to run the Telegram bot\n\n")
        f.write("# Activate virtual environment if it exists\n")
        f.write("if [ -d \"venv\" ]; then\n")
        f.write("    source venv/bin/activate\n")
        f.write("fi\n\n")
        f.write("# Load environment variables from .env file\n")
        f.write("export $(grep -v '^#' .env | xargs)\n\n")
        f.write("# Run the bot\n")
        f.write("python ultra_simple_bot.py\n")
    
    # Make run script executable
    os.chmod(os.path.join(target_dir, "run_bot.sh"), 0o755)
    
    # Create a setup script
    with open(os.path.join(target_dir, "setup.sh"), "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# Setup script for the Telegram bot\n\n")
        f.write("# Create virtual environment\n")
        f.write("python -m venv venv\n")
        f.write("source venv/bin/activate\n\n")
        f.write("# Install dependencies\n")
        f.write("pip install -r requirements.txt\n\n")
        f.write("# Create .env file from example if it doesn't exist\n")
        f.write("if [ ! -f \".env\" ]; then\n")
        f.write("    cp .env.example .env\n")
        f.write("    echo \"Please edit .env file with your bot token and database credentials\"\n")
        f.write("fi\n")
    
    # Make setup script executable
    os.chmod(os.path.join(target_dir, "setup.sh"), 0o755)
    
    print(f"\nDeployment package created in {target_dir}")
    print("To deploy the bot on your server:")
    print("1. Copy the deployment_package folder to your server")
    print("2. Run ./setup.sh to set up the environment")
    print("3. Edit the .env file with your bot token")
    print("4. Run ./run_bot.sh to start the bot")

if __name__ == "__main__":
    create_deployment_package()