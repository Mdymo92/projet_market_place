"""Spark Structured Streaming: every Kafka topic -> Delta table in the lake raw zone (volet 2 + 4).

- keeps the original JSON untouched (raw zone rule: never modified), plus Kafka metadata
- partitioned by topic and ingestion date
- checkpoint on MinIO: kill the job, restart it, it resumes from the last committed offsets
- Delta sink + checkpoint = exactly-once into the lake (see ADR on delivery guarantees)

Next jobs (owner: Ilyes): raw -> staging (typing, dedup on event_id, email hashing),
windows + watermark for KPIs and alerts -> consumption + topic alerts.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

TOPICS = "clicks,orders,payments,inventory,shipments,product_updated"
RAW_PATH = "s3a://raw/events"
CHECKPOINT = "s3a://checkpoints/kafka_to_raw"


def main() -> None:
    import os

    spark = SparkSession.builder.appName("kafka_to_raw").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP", "kafka:9092"))
        .option("subscribe", TOPICS)
        .option("startingOffsets", "earliest")
        .option("maxOffsetsPerTrigger", 50_000)  # back-pressure during Black Friday mode
        .load()
    )

    raw = stream.select(
        F.col("topic"),
        F.col("partition").alias("kafka_partition"),
        F.col("offset").alias("kafka_offset"),
        F.col("timestamp").alias("kafka_ts"),
        F.col("key").cast("string").alias("key"),
        F.col("value").cast("string").alias("value"),
        F.get_json_object(F.col("value").cast("string"), "$.event_id").alias("event_id"),
        F.current_timestamp().alias("ingested_at"),
    ).withColumn("ingest_date", F.to_date("ingested_at"))

    query = (
        raw.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", CHECKPOINT)
        .partitionBy("topic", "ingest_date")
        .trigger(processingTime="10 seconds")
        .queryName("kafka_to_raw")
        .start(RAW_PATH)
    )
    query.awaitTermination()


if __name__ == "__main__":
    main()
