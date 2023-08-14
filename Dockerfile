FROM python:3.10-slim

WORKDIR /home/app


COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app/ app/

# terrible temp solution
COPY ".env" ".env"

CMD ["python", "app/main.py"]
