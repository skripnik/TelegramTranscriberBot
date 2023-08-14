#!/bin/bash

PROCESS_NAME="telegram-bot-api"
PIDS=$(ps -eaf | grep "$PROCESS_NAME" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
  echo "No processes found with name $PROCESS_NAME"
else
  for PID in $PIDS; do
    echo "Found process $PID. Killing now..."
    kill -9 "$PID"
  done
fi
