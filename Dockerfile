# Use a single base image for both stages to minimize the number of base layers.
FROM python:3.10-slim as base

WORKDIR /home/tgbot
ENV PYTHONPATH="/home/tgbot"

# Install system dependencies which are unlikely to change frequently.
RUN apt update && \
    apt install -y --no-install-recommends \
        ffmpeg \
        make \
        git \
        zlib1g-dev \
        libssl-dev \
        gperf \
        cmake \
        g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies.
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Compile telegram-bot-api.
COPY . /home/tgbot/
WORKDIR /home/tgbot/telegram-bot-api/build

RUN cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=.. ..
RUN cmake --build . --target install

COPY run.sh /home/tgbot/run.sh

CMD ["/bin/sh","/home/tgbot/run.sh"]
