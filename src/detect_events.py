import os
import glob
import pandas as pd

def get_latest_spark_csv(spark_output_dir):
    csv_files = glob.glob(os.path.join(spark_output_dir, "part-*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Nie znaleziono pliku wynikowego Sparka w katalogu: {spark_output_dir}")
    return csv_files[0]

def main():
    print("Uruchamianie modułu detekcji zdarzeń...")

    spark_input_dir = "data/processed/hourly_weather"
    output_events_path = "data/processed/events.csv"

    try:
        spark_csv_file = get_latest_spark_csv(spark_input_dir)
        print(f"Wczytywanie danych godzinowych z pliku: {spark_csv_file}")
        df = pd.read_csv(spark_csv_file)
    except Exception as e:
        print(f"Błąd podczas ładowania danych: {e}")
        return

    print("Analizowanie warunków pogodowych...")
    detected_events = []

    for index, row in df.iterrows():
        hour = row['hour']
        station_id = row['station_id']
        temp_avg = row['temp_avg']
        wind_max = row['wind_max']
        rain_sum = row['rain_sum']
        humidity_avg = row['humidity_avg']
        pressure_avg = row['pressure_avg']

        # Heavy Rain
        if rain_sum >= 10.0:
            detected_events.append({"time": hour, "station_id": station_id, "event": "Heavy Rain", "details": f"Opady: {rain_sum} mm"})

        # Strong Wind
        if wind_max >= 50.0:
            detected_events.append({"time": hour, "station_id": station_id, "event": "Strong Wind", "details": f"Wiatr: {wind_max} km/h"})

        # Heat Wave & Frost
        if temp_avg >= 30.0:
            detected_events.append({"time": hour, "station_id": station_id, "event": "Heat Wave", "details": f"Temperatura: {temp_avg}°C"})
        if temp_avg <= 0.0:
            detected_events.append({"time": hour, "station_id": station_id, "event": "Frost Alert", "details": f"Temperatura: {temp_avg}°C"})

        # Low Pressure (Storm Risk)
        if pressure_avg < 1000.0:
            detected_events.append({"time": hour, "station_id": station_id, "event": "Low Pressure / Storm Risk", "details": f"Ciśnienie: {pressure_avg} hPa"})

        # High Humidity
        if humidity_avg > 90.0:
            detected_events.append({"time": hour, "station_id": station_id, "event": "High Humidity", "details": f"Wilgotność: {humidity_avg}%"})

    if detected_events:
        events_df = pd.DataFrame(detected_events)
        events_df = events_df.sort_values(by="time")
        
        print("\nWykryte zdarzenia pogodowe:")
        print(events_df.to_string(index=False))
        
        os.makedirs(os.path.dirname(output_events_path), exist_ok=True)
        events_df.to_csv(output_events_path, index=False)
        print(f"\nOś czasu zdarzeń zapisana pomyślnie w: {output_events_path}")
    else:
        print("\nW tym dniu nie wykryto żadnych anomalii ani ważnych zdarzeń pogodowych.")
        empty_df = pd.DataFrame(columns=["time", "station_id", "event", "details"])
        empty_df.to_csv(output_events_path, index=False)

if __name__ == "__main__":
    main()