import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, ArrayType

def main():
    # 1. Inicjalizacja sesji Sparka
    spark = SparkSession.builder \
        .appName("WeatherHourlyAggregation") \
        .master("local[*]") \
        .getOrCreate()
    
    print("Uruchomiono sesję Spark...")

    # Ścieżki do plików
    raw_data_path = "data/raw/"
    output_data_path = "data/processed/hourly_weather"

    # 2. Definicja dopasowanego schematu zagnieżdżonego do struktury API
    # Odzwierciedlamy tablice znajdujące się wewnątrz obiektu "hourly"
    hourly_schema = StructType([
        StructField("time", ArrayType(StringType()), True),
        StructField("temperature_2m", ArrayType(DoubleType()), True),
        StructField("precipitation", ArrayType(DoubleType()), True),
        StructField("wind_speed_10m", ArrayType(DoubleType()), True)
    ])

    api_schema = StructType([
        StructField("hourly", hourly_schema, True)
    ])

    # 3. Odczyt surowych danych JSON
    print(f"Wczytywanie surowych danych z: {raw_data_path}")
    raw_df = spark.read.schema(api_schema).json(raw_data_path)

    if raw_df.rdd.isEmpty():
        print("Brak danych w katalogu data/raw/! Przerwanie działania.")
        return

    # 4. Spłaszczanie danych (Exploding arrays)
    # Ponieważ tablice w sekcji 'hourly' są równoległe (ten sam indeks oznacza tę samą godzinę),
    # używamy posexplode na osi czasu, a wartości z pozostałych tablic wyciągamy po indeksie (pos).
    exploded_df = raw_df.select(F.posexplode("hourly.time").alias("pos", "timestamp"), "hourly") \
        .withColumn("temperature", F.col("hourly.temperature_2m").getItem(F.col("pos"))) \
        .withColumn("rain_mm", F.col("hourly.precipitation").getItem(F.col("pos"))) \
        .withColumn("wind_speed", F.col("hourly.wind_speed_10m").getItem(F.col("pos"))) \
        .withColumn("station_id", F.lit("POZ_01")) # Dodajemy sztuczne ID stacji (np. Poznań), skoro brak go w JSON

    # 5. Przetwarzanie i konwersja typów (Timestamp normalization)
    # Formaty dat z API ("2026-06-16T00:00") parsujemy na właściwy Timestamp
    clean_df = exploded_df.withColumn("dt", F.to_timestamp("timestamp", "yyyy-MM-dd'T'HH:mm"))

    # 6. Agregacje godzinowe przy użyciu okna czasowego Sparka
    # Twoje dane z API są już w interwałach godzinnych, ale agregacja grupuje je poprawnie
    # i zabezpiecza strukturę pod kątem wymogów projektu nr 9
    print("Przetwarzanie agregacji godzinowych...")
    hourly_aggregated_df = clean_df \
        .groupBy(
            F.window("dt", "1 hour").alias("time_window"),
            "station_id"
        ) \
        .agg(
            F.round(F.avg("temperature"), 1).alias("temp_avg"),
            F.round(F.max("wind_speed"), 1).alias("wind_max"),
            F.round(F.sum("rain_mm"), 1).alias("rain_sum")
            # Usunięto brakujące z API kolumny: humidity i pressure, aby kod się nie wywracał
        )

    # Wyciągamy czytelną datę rozpoczęcia okna jako kolumnę tekstową 'hour'
    final_df = hourly_aggregated_df \
        .withColumn("hour", F.date_format("time_window.start", "yyyy-MM-dd HH:mm")) \
        .select("hour", "station_id", "temp_avg", "wind_max", "rain_sum") \
        .orderBy("hour")

    # Pokazujemy podgląd w konsoli podczas debugowania
    print("Podgląd przetworzonych danych:")
    final_df.show(10, truncate=False)

    # 7. Zapis wyników do formatu CSV dla kolejnego skryptu
    print(f"Zapisywanie przetworzonych danych do: {output_data_path}")
    
    final_df.coalesce(1).write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(output_data_path)

    # Zamykamy sesję Sparka
    spark.stop()
    print("Proces zakończony sukcesem!")

if __name__ == "__main__":
    main()