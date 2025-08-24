import os
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_json, struct, lit, current_timestamp
)
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
REDDIT_DATA_TOPIC = "reddit-data"
TICKER_MENTIONS_TOPIC = "ticker-mentions"

class SparkRedditProcessor:
    def __init__(self):
        self.spark = None
        self.setup_spark()
        
    def setup_spark(self):
        """Initialize Spark session with Kafka support"""
        
        self.spark = SparkSession.builder \
            .appName("RedditTickerExtractor") \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        # Set log level to reduce noise
        self.spark.sparkContext.setLogLevel("WARN")
        
        print("✅ Spark session created successfully")
    
    def get_reddit_data_schema(self):
        """Define schema for Reddit data from Kafka"""
        return StructType([
            StructField("id", StringType(), True),
            StructField("subreddit", StringType(), True),
            StructField("body", StringType(), True),
            StructField("timestamp", StringType(), True),
            StructField("type", StringType(), True)
        ])
    
    def process_stream(self):
        """Main streaming process"""
        print("🚀 Starting Spark streaming process...")
        
        # Read from Kafka topic
        df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
            .option("subscribe", REDDIT_DATA_TOPIC) \
            .option("startingOffsets", "latest") \
            .load()
        
        print(f"📖 Reading from Kafka topic: {REDDIT_DATA_TOPIC}")
        
        # Parse JSON data
        reddit_schema = self.get_reddit_data_schema()
        
        parsed_df = df.select(
            col("key").cast("string").alias("kafka_key"),
            from_json(col("value").cast("string"), reddit_schema).alias("data")
        ).select(
            "kafka_key",
            "data.*"
        )
        
        # Add processed field - placeholder for ticker extraction
        processed_df = parsed_df \
            .withColumn("processed", lit(True)) \
            .withColumn("processed_timestamp", current_timestamp())
        
        # Create final output structure
        output_df = processed_df.select(
            col("subreddit").alias("kafka_key"),
            to_json(struct(
                col("id"),
                col("subreddit"),
                col("body"),
                col("timestamp"),
                col("type"),
                col("processed"),
                col("processed_timestamp").cast("string").alias("processed_timestamp")
            )).alias("value")
        )
        
        # Write to ticker mentions topic
        query = output_df \
            .writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
            .option("topic", TICKER_MENTIONS_TOPIC) \
            .option("checkpointLocation", "/tmp/spark-checkpoint") \
            .outputMode("append") \
            .trigger(processingTime="10 seconds") \
            .start()
        
        print(f"📝 Writing processed data to: {TICKER_MENTIONS_TOPIC}")
        print("✅ Streaming started successfully!")
        print("📊 Processing Reddit data (adding processed: True)")
        print("Press Ctrl+C to stop the stream")
        
        # Wait for the streaming to finish
        try:
            query.awaitTermination()
        except KeyboardInterrupt:
            print("\n⏹️  Stopping Spark streaming...")
            query.stop()
            self.spark.stop()
            print("✅ Spark streaming stopped successfully")

def main():
    """Main function to run the Spark processor"""
    processor = SparkRedditProcessor()
    processor.process_stream()

if __name__ == "__main__":
    main()