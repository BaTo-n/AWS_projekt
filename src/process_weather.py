import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, ArrayType

def main():
    spark = SparkSession.builder \
        .appName("WeatherHourlyAggregation") \
        .master("local[*]") \
        .getOrCreate()
    
    print("Uruchomiono sesję Spark...")

    raw_data_path = "data/raw/"
    output_data_path = "data/processed/hourly_weather"

    hourly_schema = StructType([
        StructField("time", ArrayType(StringType()), True),
        StructField("temperature_2m", ArrayType(DoubleType()), True),
        StructField("precipitation", ArrayType(DoubleType()), True),
        StructField("wind_speed_10m", ArrayType(DoubleType()), True)
    ])

    api_schema = StructType([
        StructField("hourly", hourly_schema, True)
    ])

    print(f"Wczytywanie surowych danych z: {raw_data_path}")
    # KLUCZOWA ZMIANA: Dodana opcja multiLine, aby poprawnie sparsować sformatowany plik JSON
    raw_df = spark.read.option("multiLine", "true").schema(api_schema).json(raw_data_path)

    if raw_df.rdd.isEmpty():
        print("Brak danych w katalogu data/raw/! Przerwanie działania.")
        return

    exploded_df = raw_df.select(F.posexplode("hourly.time").alias("pos", "timestamp"), "hourly") \
        .withColumn("temperature", F.col("hourly.temperature_2m")[F.col("pos")]) \
        .withColumn("rain_mm", F.col("hourly.precipitation")[F.col("pos")]) \
        .withColumn("wind_speed", F.col("hourly.wind_speed_10m")[F.col("pos")]) \
        .withColumn("station_id", F.lit("POZ_01"))

    clean_df = exploded_df.withColumn("dt", F.to_timestamp("timestamp", "yyyy-MM-dd'T'HH:mm"))

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
        )

    final_df = hourly_aggregated_df \
        .withColumn("hour", F.date_format("time_window.start", "yyyy-MM-dd HH:mm")) \
        .select("hour", "station_id", "temp_avg", "wind_max", "rain_sum") \
        .orderBy("hour")

    print("Podgląd przetworzonych danych:")
    final_df.show(10, truncate=False)

    print(f"Zapisywanie przetworzonych danych do: {output_data_path}")
    final_df.coalesce(1).write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(output_data_path)

    spark.stop()
    print("Proces zakończony sukcesem!")

if __name__ == "__main__":
    main()