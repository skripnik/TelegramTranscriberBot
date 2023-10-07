# Use a single base image for both stages to minimize the number of base layers.
FROM python:3.10-slim as base

CMD ["/bin/sh","/home/tgbot/run.sh"]

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

WORKDIR /home/tgbot/
RUN git clone --recursive https://github.com/tdlib/telegram-bot-api.git
RUN mkdir telegram-bot-api/build \
    && cd telegram-bot-api/build \
    && cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=.. .. \
    && cmake --build . --target install

# Install Python dependencies.
ENV PYTHONPATH="/home/tgbot"
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Compile telegram-bot-api.
COPY . /home/tgbot/
