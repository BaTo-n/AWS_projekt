import os
import glob
import pandas as pd

def get_latest_spark_csv(spark_output_dir):
    """
    Spark zapisuje pliki w katalogu jako part-*.csv.
    Ta funkcja znajduje właściwy plik CSV wewnątrz wskazanego folderu.
    """
    csv_files = glob.glob(os.path.join(spark_output_dir, "part-*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Nie znaleziono pliku wynikowego Sparka w katalogu: {spark_output_dir}")
    # Zwracamy pierwszy znaleziony plik (przy coalesce(1) będzie tylko jeden główny)
    return csv_files[0]

def main():
    print("Uruchamianie modułu detekcji zdarzeń (System Ekspercki)...")

    # Ścieżki do plików
    spark_input_dir = "data/processed/hourly_weather"
    output_events_path = "data/processed/events.csv"

    # 1. Wczytanie danych przetworzonych przez Sparka
    try:
        spark_csv_file = get_latest_spark_csv(spark_input_dir)
        print(f"Wczytywanie danych godzinowych z pliku: {spark_csv_file}")
        df = pd.read_csv(spark_csv_file)
    except Exception as e:
        print(f"Błąd podczas ładowania danych: {e}")
        print("Upewnij się, że skrypt 'process_weather.py' został uruchomiony jako pierwszy.")
        return

    # 2. Definicja reguł systemu eksperckiego (Expert Rules / Threshold Evaluation)
    print("Analizowanie warunków pogodowych pod kątem zdarzeń...")
    detected_events = []

    # Iterujemy po każdym wierszu (godzinie) w danych pogodowych
    for index, row in df.iterrows():
        hour = row['hour']
        station_id = row['station_id']
        temp_avg = row['temp_avg']
        wind_max = row['wind_max']
        rain_sum = row['rain_sum']

        # Reguła 1: Gwałtowny/Silny opad (Heavy Rain)
        if rain_sum >= 10.0:
            detected_events.append({
                "time": hour,
                "station_id": station_id,
                "event": "Heavy Rain",
                "details": f"Opady: {rain_sum} mm"
            })

        # Reguła 2: Silny wiatr (Strong Wind)
        if wind_max >= 50.0:
            detected_events.append({
                "time": hour,
                "station_id": station_id,
                "event": "Strong Wind",
                "details": f"Wiatr: {wind_max} km/h"
            })

        # Reguła 3: Fala upałów (Heat Wave)
        if temp_avg >= 30.0:
            detected_events.append({
                "time": hour,
                "station_id": station_id,
                "event": "Heat Wave",
                "details": f"Temperatura: {temp_avg}°C"
            })
            
        # Reguła Dodatkowa: Przymrozek (Frost Alert) - warto dodać coś od siebie!
        if temp_avg <= 0.0:
            detected_events.append({
                "time": hour,
                "station_id": station_id,
                "event": "Frost Alert",
                "details": f"Temperatura: {temp_avg}°C"
            })

    # 3. Tworzenie i zapisywanie osi czasu zdarzeń (Daily Event Timeline)
    if detected_events:
        events_df = pd.DataFrame(detected_events)
        
        # Sortujemy chronologicznie
        events_df = events_df.sort_values(by="time")
        
        print("\nWykryte zdarzenia pogodowe:")
        print(events_df.to_string(index=False))
        
        # Zapewniamy, że katalog docelowy istnieje i zapisujemy CSV
        os.makedirs(os.path.dirname(output_events_path), exist_ok=True)
        events_df.to_csv(output_events_path, index=False)
        print(f"\nOś czasu zdarzeń zapisana pomyślnie w: {output_events_path}")
    else:
        print("\nW tym dniu nie wykryto żadnych anomalii ani ważnych zdarzeń pogodowych.")
        # Zapisujemy pusty plik z nagłówkami, żeby generate_report.py się nie wywalił
        empty_df = pd.DataFrame(columns=["time", "station_id", "event", "details"])
        empty_df.to_csv(output_events_path, index=False)

if __name__ == "__main__":
    main()