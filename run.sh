/home/tgbot/telegram-bot-api/bin/telegram-bot-api \
    --local -v 2 \
    --api-hash="${TELEGRAM_API_HASH}" \
    --api-id="${TELEGRAM_API_ID}" & \
python "/home/tgbot/app/main.py"
