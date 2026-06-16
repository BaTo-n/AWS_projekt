FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y default-jre-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY run_pipeline.py .

CMD ["python", "run_pipeline.py"]