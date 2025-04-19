#!/bin/bash
# Setup script for the Telegram bot

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Please edit .env file with your bot token and database credentials"
fi
