import os
import glob
import pandas as pd
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def get_latest_spark_csv(spark_output_dir):
    csv_files = glob.glob(os.path.join(spark_output_dir, "part-*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Nie znaleziono danych godzinowych w: {spark_output_dir}")
    return csv_files[0]

def main():
    print("Generowanie raportu końcowego oraz wykresów...")

    spark_input_dir = "data/processed/hourly_weather"
    events_input_path = "data/processed/events.csv"
    report_output_path = "reports/daily_report.txt"
    chart_output_path = "reports/daily_weather_chart.png"

    os.makedirs("reports", exist_ok=True)

    try:
        spark_csv = get_latest_spark_csv(spark_input_dir)
        df_hourly = pd.read_csv(spark_csv)
        df_events = pd.read_csv(events_input_path)
    except Exception as e:
        print(f"Błąd podczas ładowania danych: {e}")
        return

    if df_hourly.empty:
        print("Brak danych do wygenerowania raportu.")
        return

    sample_date = df_hourly['hour'].iloc[0].split()[0]
    station_id = df_hourly['station_id'].iloc[0]

    #temp
    temp_mean = round(df_hourly['temp_avg'].mean(), 1)
    temp_max = df_hourly['temp_avg'].max()
    temp_min = df_hourly['temp_avg'].min()

    #wilgoc
    hum_mean = round(df_hourly['humidity_avg'].mean(), 1)
    hum_max = df_hourly['humidity_avg'].max()
    hum_min = df_hourly['humidity_avg'].min()

    #cisnienie
    press_mean = round(df_hourly['pressure_avg'].mean(), 1)
    press_max = df_hourly['pressure_avg'].max()
    press_min = df_hourly['pressure_avg'].min()

    #chmury
    cloud_mean = round(df_hourly['cloud_avg'].mean(), 1)
    cloud_max = df_hourly['cloud_avg'].max()
    cloud_min = df_hourly['cloud_avg'].min()

    #wiatr+deszcz
    wind_max_day = df_hourly['wind_max'].max()
    total_rain = round(df_hourly['rain_sum'].sum(), 1)

    print(f"Rysowanie wykresu do pliku: {chart_output_path} ...")
    
    df_hourly['hour_dt'] = pd.to_datetime(df_hourly['hour'])

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14), sharex=True)
    fig.suptitle(f"Raport Pogodowy: {station_id} ({sample_date})", fontsize=16)

    ax1.plot(df_hourly['hour_dt'], df_hourly['temp_avg'], color='red', marker='o', label='Temp (°C)')
    ax1.set_ylabel('Temperatura (°C)', color='red')
    ax1.tick_params(axis='y', labelcolor='red')
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    ax1_twin = ax1.twinx()
    ax1_twin.plot(df_hourly['hour_dt'], df_hourly['humidity_avg'], color='blue', linestyle='--', label='Wilgotność (%)')
    ax1_twin.set_ylabel('Wilgotność (%)', color='blue')
    ax1_twin.tick_params(axis='y', labelcolor='blue')

    ax2.plot(df_hourly['hour_dt'], df_hourly['pressure_avg'], color='green', marker='s', label='Ciśnienie (hPa)')
    ax2.set_ylabel('Ciśnienie (hPa)', color='green')
    ax2.tick_params(axis='y', labelcolor='green')
    ax2.grid(True, linestyle='--', alpha=0.5)

    ax2_twin = ax2.twinx()
    ax2_twin.fill_between(df_hourly['hour_dt'], df_hourly['cloud_avg'], color='gray', alpha=0.3, label='Zachmurzenie (%)')
    ax2_twin.set_ylabel('Zachmurzenie (%)', color='gray')

    ax3.bar(df_hourly['hour_dt'], df_hourly['rain_sum'], color='cyan', alpha=0.7, width=0.03, label='Opady (mm)')
    ax3.set_ylabel('Opady (mm)', color='cyan')
    ax3.tick_params(axis='y', labelcolor='cyan')
    ax3.grid(True, linestyle='--', alpha=0.5)

    ax3_twin = ax3.twinx()
    ax3_twin.plot(df_hourly['hour_dt'], df_hourly['wind_max'], color='purple', marker='^', label='Wiatr (km/h)')
    ax3_twin.set_ylabel('Wiatr (km/h)', color='purple')
    ax3_twin.tick_params(axis='y', labelcolor='purple')

    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(chart_output_path)
    plt.close()

    report_lines = []
    report_lines.append("==================================================")
    report_lines.append(f" AUTOMATIC WEATHER ANALYSIS REPORT - {sample_date}")
    report_lines.append("==================================================")
    report_lines.append(f"Station ID:         {station_id}")
    report_lines.append(f"Generated at:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Chart Attached:     {os.path.basename(chart_output_path)}")
    report_lines.append("--------------------------------------------------")
    report_lines.append("1. DAILY METRICS SUMMARY (RANGES)")
    report_lines.append("--------------------------------------------------")
    
    report_lines.append(f"{'PARAMETER':<16} | {'MIN':<8} | {'MEAN':<8} | {'MAX':<8}")
    report_lines.append("-" * 50)
    report_lines.append(f"{'Temperature (°C)':<16} | {temp_min:<8} | {temp_mean:<8} | {temp_max:<8}")
    report_lines.append(f"{'Humidity (%)':<16} | {hum_min:<8} | {hum_mean:<8} | {hum_max:<8}")
    report_lines.append(f"{'Pressure (hPa)':<16} | {press_min:<8} | {press_mean:<8} | {press_max:<8}")
    report_lines.append(f"{'Cloud Cover (%)':<16} | {cloud_min:<8} | {cloud_mean:<8} | {cloud_max:<8}")
    report_lines.append("-" * 50)
    report_lines.append(f"-> Max Wind Speed:       {wind_max_day} km/h")
    report_lines.append(f"-> Total Daily Rainfall: {total_rain} mm")
    report_lines.append("--------------------------------------------------")
    report_lines.append("2. DETECTED WEATHER EVENTS & ANOMALIES")
    report_lines.append("--------------------------------------------------")

    if df_events.empty:
        report_lines.append("No significant or dangerous weather events detected.")
        report_lines.append("The day was meteorologically stable.")
    else:
        report_lines.append(f"Total events detected: {len(df_events)}")
        report_lines.append("")
        for index, row in df_events.iterrows():
            time_hm = row['time'].split()[1] if " " in str(row['time']) else row['time']
            report_lines.append(f"  [{time_hm}] ALERT: {row['event']} -> {row['details']}")

    full_report = "\n".join(report_lines)

    print("\n-------- RAPORT --------")
    print(full_report)
    print("------------------------------\n")

    with open(report_output_path, "w", encoding="utf-8") as f:
        f.write(full_report)

    print(f"Raport końcowy został pomyślnie zapisany w: {report_output_path}")

if __name__ == "__main__":
    main()