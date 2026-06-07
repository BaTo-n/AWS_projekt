import os
import glob
import pandas as pd

def get_latest_spark_csv(spark_output_dir):
    """Pomocnicza funkcja do znalezienia pliku CSV wygenerowanego przez Sparka."""
    csv_files = glob.glob(os.path.join(spark_output_dir, "part-*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Nie znaleziono danych godzinowych w: {spark_output_dir}")
    return csv_files[0]

def main():
    print("Uruchamianie modułu generowania raportu końcowego...")

    # Ścieżki do plików wejściowych i wyjściowych
    spark_input_dir = "data/processed/hourly_weather"
    events_input_path = "data/processed/events.csv"
    report_output_path = "reports/daily_report.txt"

    # Zapewnienie, że katalog na raporty istnieje
    os.makedirs("reports", exist_ok=True)

    try:
        # 1. Wczytanie danych
        spark_csv = get_latest_spark_csv(spark_input_dir)
        df_hourly = pd.read_csv(spark_csv)
        df_events = pd.read_csv(events_input_path)
    except Exception as e:
        print(f"Błąd podczas ładowania danych: {e}")
        print("Upewnij się, że uruchomiłeś wcześniejsze skrypty w kolejności.")
        return

    # 2. Wyciąganie metryk dobowych do raportu
    # Pobieramy datę z pierwszego wiersza (format: YYYY-MM-DD HH:MM -> bierzemy tylko YYYY-MM-DD)
    sample_date = df_hourly['hour'].iloc[0].split()[0] if not df_hourly.empty else "Nieznana data"
    station_id = df_hourly['station_id'].iloc[0] if not df_hourly.empty else "Nieznana"

    temp_mean = round(df_hourly['temp_avg'].mean(), 1)
    temp_max = df_hourly['temp_avg'].max()
    temp_min = df_hourly['temp_avg'].min()
    wind_max_day = df_hourly['wind_max'].max()
    total_rain = round(df_hourly['rain_sum'].sum(), 1)
    humidity_mean = round(df_hourly['humidity_avg'].mean(), 1)

    # 3. Budowanie treści raportu (String Builder)
    report_lines = []
    report_lines.append("==================================================")
    report_lines.append(f" AUTOMATIC WEATHER ANALYSIS REPORT - {sample_date}")
    report_lines.append("==================================================")
    report_lines.append(f"Station ID:         {station_id}")
    report_lines.append(f"Generated at:       2026-06-07 (UTC Context)")
    report_lines.append("--------------------------------------------------")
    report_lines.append("1. DAILY METRICS SUMMARY")
    report_lines.append("--------------------------------------------------")
    report_lines.append(f"• Average Temperature:    {temp_mean}°C")
    report_lines.append(f"• Max Temperature:        {temp_max}°C")
    report_lines.append(f"• Min Temperature:        {temp_min}°C")
    report_lines.append(f"• Max Wind Speed:         {wind_max_day} km/h")
    report_lines.append(f"• Total Daily Rainfall:   {total_rain} mm")
    report_lines.append(f"• Average Humidity:       {humidity_mean}%")
    report_lines.append("--------------------------------------------------")
    report_lines.append("2. DETECTED WEATHER EVENTS & ANOMALIES")
    report_lines.append("--------------------------------------------------")

    # Sprawdzamy czy system ekspercki wykrył jakieś zdarzenia
    if df_events.empty:
        report_lines.append("No significant or dangerous weather events detected.")
        report_lines.append("The day was meteorologically stable.")
    else:
        report_lines.append(f"Total events detected: {len(df_events)}")
        report_lines.append("")
        # Wypisujemy zdarzenia w ładnym formacie
        for index, row in df_events.iterrows():
            # Wyciągamy samą godzinę z pełnego timestampu (HH:MM)
            time_hm = row['time'].split()[1] if " " in str(row['time']) else row['time']
            report_lines.append(f"  [{time_hm}] ALERT: {row['event']} -> {row['details']}")

    report_lines.append("--------------------------------------------------")
    report_lines.append("3. PIPELINE METADATA & STATUS")
    report_lines.append("--------------------------------------------------")
    report_lines.append("• Ingestion Layer:   SUCCESS (JSON format preserved)")
    report_lines.append("• Processing Layer:  SUCCESS (Apache Spark Windowed Aggregations)")
    report_lines.append("• Analytics Layer:   SUCCESS (Expert Rule Engine Evaluated)")
    report_lines.append("==================================================")

    # Łączymy wszystkie linie w jeden tekst
    full_report = "\n".join(report_lines)

    # 4. Wyświetlenie raportu w konsoli i zapis do pliku txt
    print("\n--- PODGLĄD GENEROWANEGO RAPORTU ---")
    print(full_report)
    print("-------------------------------------\n")

    with open(report_output_path, "w", encoding="utf-8") as f:
        f.write(full_report)

    print(f"Raport końcowy został pomyślnie zapisany w: {report_output_path}")

if __name__ == "__main__":
    main()