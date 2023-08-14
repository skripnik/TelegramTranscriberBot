#!/bin/bash
source .env

WORKING_DIR="$(pwd)/telegram-bot-api-data"
TEMP_DIR="$(pwd)/telegram-bot-api-temp"

mkdir -p "$WORKING_DIR"
mkdir -p "$TEMP_DIR"

echo "Running Telegram Bot API Server... To stop the server run: bash stop_telegram_server"
telegram-bot-api/bin/telegram-bot-api --local --verbosity=3 --api-id="$TELEGRAM_API_ID" --api-hash="$TELEGRAM_API_HASH" --dir="$WORKING_DIR" --temp-dir="$TEMP_DIR"
