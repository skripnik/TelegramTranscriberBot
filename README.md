## Installation

You will need a server with root access. Code samples are for Ubuntu. On different systems, you may need to use
different commands.

Update the system

```bash
sudo apt-get update
sudo apt-get upgrade
```

Copy this repository

```bash
git clone https://github.com/skripnik/TelegramTranscriberBot.git
cd TelegramTranscriberBot
```

Install [Telegram Bot Server](https://github.com/tdlib/telegram-bot-api) in TelegramTranscriberBot. For the actual code
use [Server build instructions generator](https://tdlib.github.io/telegram-bot-api/build.html). Building requires abot
4GB of RAM and it can take up to 1 hour.

```bash
sudo apt-get install make git zlib1g-dev libssl-dev gperf cmake g++
git clone --recursive https://github.com/tdlib/telegram-bot-api.git
cd telegram-bot-api
rm -rf build
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=.. ..
cmake --build . --target install
cd ../..
ls -l telegram-bot-api/bin/telegram-bot-api*
```

Install [FFMPEG](https://www.ffmpeg.org/)

```bash
sudo apt install ffmpeg
```

Get required access keys:

- Register a Telegram Bot using [@BotFather](https://t.me/botfather) and get the Telegram Bot Token
- Create a Telegram app and get api_id and api_hash ([Tutorial](https://core.telegram.org/api/obtaining_api_id))
- Register in OpenAI Platform
  and [get the OpenAI API Key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key)

Create a .env file in TelegramTranscriberBot fodler, add the following variables (don't forget to replace the values
with your own):

```bash
cat <<EOF > .env
TELEGRAM_API_TOKEN="*********:***********************"
TELEGRAM_API_ID="*********"
TELEGRAM_API_HASH="********************************"
OPENAI_API_KEY="sk-***************************"
EOF
```

Run the server:

```bash
bash start_telegram_server.sh
```

Install Python, pip and dependencies:

```bash
sudo apt install python3 python3-pip
pip install -r requirements.txt
```

Run the bot:

```bash
python3 app/main.py
```

## Updates

```bash
cd TelegramTranscriberBot
git pull
```