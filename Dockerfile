FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY req.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r req.txt

COPY src/libs/pdf_text-0.1.0-cp312-cp312-manylinux_2_34_x86_64.whl /app/libs/
RUN pip install /app/libs/pdf_text-0.1.0-cp312-cp312-manylinux_2_34_x86_64.whl


COPY . .

CMD ["python", "main.py"]
