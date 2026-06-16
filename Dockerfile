# Używamy oficjalnego obrazu Pythona
FROM python:3.11-slim

# Instalacja Javy (niezbędnej do działania PySparka)
RUN apt-get update && \
    apt-get install -y default-jre-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie i instalacja zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu źródłowego
COPY src/ ./src/
COPY run_pipeline.py .

# Domyślna komenda po uruchomieniu kontenera
CMD ["python", "run_pipeline.py"]