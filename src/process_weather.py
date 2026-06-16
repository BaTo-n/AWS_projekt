import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, ArrayType, LongType

def main():
    spark = SparkSession.builder \
        .appName("WeatherHourlyAggregation") \
        .master("local[*]") \
        .getOrCreate()
    
    print("Uruchomiono sesję Spark...")

    raw_data_path = "data/raw/"
    output_data_path = "data/processed/hourly_weather"

    record_schema = StructType([
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

    api_schema = StructType([
        StructField("station_id", StringType(), True),
        StructField("count", LongType(), True),
        StructField("records", ArrayType(record_schema), True)
    ])

    print(f"Wczytywanie surowych danych z: {raw_data_path}")
    raw_df = spark.read.option("multiLine", "true").schema(api_schema).json(raw_data_path)

    if raw_df.rdd.isEmpty():
        print("Brak danych w katalogu data/raw/")
        return

    exploded_df = raw_df.select(F.explode("records").alias("record"))

    clean_df = exploded_df.select(
        F.col("record.timestamp").alias("raw_timestamp"),
        F.col("record.station_id").alias("station_id"),
        F.col("record.temperature").alias("temperature"),
        F.col("record.humidity").alias("humidity"),
        F.col("record.pressure").alias("pressure"),
        F.col("record.wind_speed").alias("wind_speed"),
        F.col("record.rain_mm").alias("rain_mm"),
        F.col("record.cloud_cover").alias("cloud_cover")
    )

    clean_df = clean_df.withColumn("dt", F.to_timestamp(F.substring("raw_timestamp", 1, 19), "yyyy-MM-dd'T'HH:mm:ss"))

    print("Przetwarzanie agregacji godzinowych...")
    hourly_aggregated_df = clean_df \
        .groupBy(
            F.window("dt", "1 hour").alias("time_window"),
            "station_id"
        ) \
        .agg(
            F.round(F.avg("temperature"), 1).alias("temp_avg"),
            F.round(F.avg("humidity"), 1).alias("humidity_avg"),
            F.round(F.avg("pressure"), 1).alias("pressure_avg"),
            F.round(F.avg("cloud_cover"), 1).alias("cloud_avg"),
            F.round(F.max("wind_speed"), 1).alias("wind_max"),
            F.round(F.sum("rain_mm"), 1).alias("rain_sum")
        )

    final_df = hourly_aggregated_df \
        .withColumn("hour", F.date_format("time_window.start", "yyyy-MM-dd HH:mm")) \
        .select("hour", "station_id", "temp_avg", "humidity_avg", "pressure_avg", "cloud_avg", "wind_max", "rain_sum") \
        .orderBy("hour")

    print("Podgląd przetworzonych danych:")
    final_df.show(5, truncate=False)

    print(f"Zapisywanie przetworzonych danych do: {output_data_path}")
    final_df.coalesce(1).write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(output_data_path)

    spark.stop()
    print("Proces zakończony sukcesem!")

if __name__ == "__main__":
    main()