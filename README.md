# Telegram Transcriber Bot

Send an audio or video file to the bot, and it will send you a transcription. It uses the OpenAI Whisper API under the
hood, so it works with many languages:

Afrikaans, Arabic, Armenian, Azerbaijani, Belarusian, Bosnian, Bulgarian, Catalan, Chinese, Croatian, Czech, Danish,
Dutch, English, Estonian, Finnish, French, Galician, German, Greek, Hebrew, Hindi, Hungarian, Icelandic, Indonesian,
Italian, Japanese, Kannada, Kazakh, Korean, Latvian, Lithuanian, Macedonian, Malay, Marathi, Maori, Nepali, Norwegian,
Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian, Spanish, Swahili, Swedish, Tagalog, Tamil,
Thai, Turkish, Ukrainian, Urdu, Vietnamese, and Welsh.

## Installation

You will need a server with root access. For the installation process, it's recommended to resize your server to at
least 4GB RAM and 2 CPUs. The higher the configuration, the faster the installation can be completed. After
installation, you can resize the server back to the original configuration.

The code samples provided are for Ubuntu. Please note that different systems may require different commands.

**1. Update the System**

```bash
sudo apt-get update
sudo apt-get upgrade
```

**2. Clone the Repository**

```bash
git clone https://github.com/skripnik/TelegramTranscriberBot.git
cd TelegramTranscriberBot
```

**3. Install [Telegram Bot Server](https://github.com/tdlib/telegram-bot-api)**

We assume that the server code will be installed in the TelegramTranscriberBot project folder.

Please refer to the [Server build instructions generator](https://tdlib.github.io/telegram-bot-api/build.html) for
actual code. Building requires about 4GB of RAM and may take up to 1 hour.

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

**4. Install [FFMPEG](https://www.ffmpeg.org/)**

```bash
sudo apt install ffmpeg
```

**5. Obtain Required Access Keys:**

- Register your Telegram Bot using [@BotFather](https://t.me/botfather), get the `api_token` and disable the bot privacy
  mode.
- Create a Telegram app to obtain your `api_id` and `api_hash`. Here's a
  useful [Tutorial](https://core.telegram.org/api/obtaining_api_id) for that.
- Register on OpenAI Platform to get
  the [OpenAI API Key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key).

**6. Configure `.env` file**

Create a .env file in the TelegramTranscriberBot folder and add the following variables. Remember to replace the
placeholders with your own values:

```bash
cat <<EOF > .env
TELEGRAM_API_TOKEN="your_telegram_bot_token"
TELEGRAM_API_ID="your_api_id"
TELEGRAM_API_HASH="your_api_hash"
OPENAI_API_KEY="your_openai_api_key"
EOF
```

**7. Start the Server**

Run the server using the following command. Note that the server will run continuously in the background. You might need
to open another console for running additional commands:

```bash
screen
bash start_telegram_server.sh
```

**8. Install Python, pip and Required Dependencies**

```bash
sudo apt install python3 python3-pip
pip install -r requirements.txt
```

**9. Run the Bot**

```bash
python3 app/main.py
```

**10. Create a Telegram group to manage users**
By default, the bot will reject any commands. To allow commands:

- Create a Telegram group (only users in this group will be allowed to use the bot)
- Add the bot to the group
- Promote the bot to administrator
- Send any message to the group
- The bot will reply with the group_id

**11. Update allowed groups in config**
Update the list of users and groups that can use the bot in `app/config.py`. Use the group_id from the previous step.

```python 
ALLOWED_TELEGRAM_CHAT_IDS = [
    -1111111111111,
]
```

**12. Restart the bot (main.py)**
Stop the python script running (usually Ctrl+C) and start it again. This time we usi it with screen, so that it will
continue running even if the SSH session is closed.

```bash
screen
python3 app/main.py
```

## Updates

Navigate to the TelegramTranscriberBot directory and pull any recent updates from the repository:

```bash
cd TelegramTranscriberBot
git pull
pip install -r requirements.txt
```

## Acknowledgements

This project was initiated and partially developed during the [Internet Without Borders](https://internetborders.net/)
hackathon. We extend our sincere thanks to the event's organizers and sponsors for their support and encouragement.

## License

This project is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0). The authors and
contributors are not liable for any damages arising from the use of this code.