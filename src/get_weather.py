import requests
import json
from datetime import datetime
from pathlib import Path

URL = "https://e6uw49pbah.execute-api.us-east-1.amazonaws.com/dev/weather/batch"
TOKEN = "TOKEN123" # <-- proszę podmienić

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

params = {
    "station_id": "GDN_01",
    "limit": 144 # doba
}

today = datetime.now().strftime("%Y-%m-%d")

print(f"Pobieranie danych z GDN_01...")
response = requests.get(URL, headers=headers, params=params)

if response.status_code != 200:
    raise Exception(f"API Error: {response.status_code}\n{response.text}")

weather_data = response.json()
project_root = Path(__file__).parent.parent

raw_dir = project_root / "data" / "raw"
raw_dir.mkdir(parents=True, exist_ok=True)

filename = raw_dir / f"weather_{today}.json"

with open(filename, "w", encoding="utf-8") as file:
    json.dump(weather_data, file, indent=4)

print(f"Dane zapisane do: {filename}")