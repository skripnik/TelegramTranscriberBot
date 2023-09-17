FROM python:3.10-slim

WORKDIR /home/tgbot
ENV PYTHONPATH="/home/tgbot"

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN apt update && \
    apt install -y --no-install-recommends ffmpeg

COPY ./ /home/tgbot/

CMD ["python", "app/main.py"]
