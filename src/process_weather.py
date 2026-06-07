import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

def main():
    # 1. Inicjalizacja sesji Sparka (lokalnie, łatwo przenaszalna na EMR)
    spark = SparkSession.builder \
        .appName("WeatherHourlyAggregation") \
        .master("local[*]") \
        .getOrCreate()
    
    print("Uruchomiono sesję Spark...")

    # Ścieżki do plików
    raw_data_path = "data/raw/"
    output_data_path = "data/processed/hourly_weather"

    # 2. Definicja schematu JSON (zgodnie z polami z dokumentacji projektu)
    # Pomaga Sparkowi szybciej parsować surowe dane z API
    weather_schema = StructType([
        StructField("timestamp", StringType(), True),
        StructField("station_id", StringType(), True),
        StructField("temperature", DoubleType(), True),
        StructField("humidity", DoubleType(), True),
        StructField("pressure", DoubleType(), True),
        StructField("wind_speed", DoubleType(), True),
        StructField("wind_direction", DoubleType(), True),
        StructField("rain_mm", DoubleType(), True),
        StructField("cloud_cover", DoubleType(), True)
    ])

    # 3. Odczyt surowych danych JSON (Persist raw data requirement)
    print(f"Wczytywanie surowych danych z: {raw_data_path}")
    raw_df = spark.read.schema(weather_schema).json(raw_data_path)

    if raw_df.rdd.isEmpty():
        print("Brak danych w katalogu data/raw/! Przerwanie działania.")
        return

    # 4. Przetwarzanie i konwersja typów (Timestamp normalization)
    # Zamieniamy string z timestampem na właściwy typ Timestamp dla operacji okienkowych
    clean_df = raw_df.withColumn("dt", F.to_timestamp("timestamp"))

    # 5. Agregacje godzinowe (Hourly aggregations za pomocą funkcji okna czasowego Sparka)
    print("Przetwarzanie agregacji godzinowych...")
    hourly_aggregated_df = clean_df \
        .groupBy(
            F.window("dt", "1 hour").alias("time_window"),
            "station_id"
        ) \
        .agg(
            F.round(F.avg("temperature"), 1).alias("temp_avg"),
            F.round(F.max("wind_speed"), 1).alias("wind_max"),
            F.round(F.sum("rain_mm"), 1).alias("rain_sum"),
            F.round(F.avg("humidity"), 1).alias("humidity_avg"),
            F.round(F.avg("pressure"), 1).alias("pressure_avg")
        )

    # Wyciągamy ładną datę rozpoczęcia okna jako kolumnę tekstową 'hour'
    final_df = hourly_aggregated_df \
        .withColumn("hour", F.date_format("time_window.start", "yyyy-MM-dd HH:mm")) \
        .select("hour", "station_id", "temp_avg", "wind_max", "rain_sum", "humidity_avg", "pressure_avg") \
        .orderBy("hour")

    # Pokazujemy podgląd w konsoli podczas debugowania
    print("Podgląd przetworzonych danych:")
    final_df.show(10, truncate=False)

    # 6. Zapis wyników do formatu CSV dla kolejnego skryptupartnera
    # coalesce(1) zbiera dane do jednego pliku CSV, aby łatwo było go odczytać w czystym Pythonie w kroku 3
    print(f"Zapisywanie przetworzonych danych do: {output_data_path}")
    
    final_df.coalesce(1).write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(output_data_path)

    # Zamykamy sesję Sparka
    spark.stop()
    print("Proces zakończny sukcesem!")

if __name__ == "__main__":
    main()