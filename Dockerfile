FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY req.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r req.txt

COPY . .

CMD ["python", "main.py"]
