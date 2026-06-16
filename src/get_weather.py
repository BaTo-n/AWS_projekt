import requests
import json
from datetime import datetime
from pathlib import Path
from pathlib import Path
from datetime import datetime



LATITUDE = 54.3706448
LONGITUDE = 18.6116557

url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LATITUDE}"
    f"&longitude={LONGITUDE}"
    f"&hourly=temperature_2m,precipitation,wind_speed_10m"
)

response = requests.get(url)

if response.status_code != 200:
    raise Exception(f"API Error: {response.status_code}")

weather_data = response.json()
project_root = Path(__file__).parent.parent

raw_dir = project_root / "data" / "raw"
raw_dir.mkdir(parents=True, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")

filename = raw_dir / f"weather_{today}.json"

with open(filename, "w", encoding="utf-8") as file:
    json.dump(weather_data, file, indent=4)

print(f"Data saved to: {filename}")