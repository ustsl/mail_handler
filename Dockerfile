FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc catdoc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src/libs/pdf_text-0.1.0-cp312-cp312-manylinux_2_34_x86_64.whl /app/src/libs/
COPY src/libs/zip_extractor-0.1.0-cp312-cp312-manylinux_2_34_x86_64.whl /app/src/libs/

COPY req.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r req.txt

COPY . .

CMD ["python", "main.py"]
