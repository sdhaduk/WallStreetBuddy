import re
import time
import shutil
from typing import List
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_json, struct, current_timestamp, window,
    udf, collect_list, explode, size
)
from pyspark.sql.types import StructType, StructField, StringType, ArrayType
import spacy
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ticker.ticker_manager import is_valid_ticker, get_ticker_from_company_name

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
REDDIT_DATA_TOPIC = "reddit-data"
TICKER_MENTIONS_TOPIC = "ticker-mentions"
CHECKPOINT_DIR = "/tmp/spark-checkpoint-new"
AMBIGUOUS_TICKERS = {
    'A', 'AM', 'BE', 'GO', 'IT', 'SO', 'AT', 'BY', 'ON', 'UP', 'IF', 'IS', 'AS', 'OR', 'TV', 'AI', 'AN', 'F', 'ALL', 'ARE', 'CAN', 'CAR', 'CAT', 'EAR', 'EYE', 'FUN', 'GET', 'HAS', 'HER', 'JOB', 'LOW', 'MAN', 'NEW', 'NOW', 'OLD', 'ONE',  'OUT', 'OWN', 'PAY', 'RUN', 'SAY', 'SEE', 'SHE', 'SIX', 'TEN', 'THE', 'TOO', 'TOP', 'TRY', 'TWO', 'USE', 'WAY', 'WHY', 'WIN', 'YES', 'YET', 'YOU', 'OLED', 'LOVE'
}

REDDIT_ONLY_TICKERS = {
    'OP', 'DD', 'PM', 'JD', 'PC', 'DTE'
}

FINANCIAL_KEYWORDS = {
    'buy', 'sell', 'hold', 'calls', 'puts', 'options', 'stock', 'shares', 'price', 'trading', 'invest', 'company', 'announced', 'quarterly', 'CEO', 'market', 'growth', 'profit', 'loss', 'dividend', 'split', 'merger', 'acquisition', 'ipo', 'earnings', 'guidance', 'analyst', 'upgrade', 'downgrade', 'target', 'valuation', 'portfolio'
}

def extract_tickers_from_text(text: str) -> List[str]:
    if not text:
        return []
    
    tickers = set()
    dollar_pattern = r'\$([A-Z]{1,5})\b'
    dollar_tickers = re.findall(dollar_pattern, text)
    
    dollar_positions = set()
    for match in re.finditer(dollar_pattern, text):
        for pos in range(match.start(), match.end()):
            dollar_positions.add(pos)
    
    for ticker in dollar_tickers:
        if is_valid_ticker(ticker):
            tickers.add(ticker)

    regular_pattern = r'\b([A-Z]{2,5})\b'
    context_score = None
    
    for match in re.finditer(regular_pattern, text):
        if any(pos in dollar_positions for pos in range(match.start(), match.end())):
            continue
        ticker = match.group(1)
        
        if ticker in tickers:
            continue
            
        if not is_valid_ticker(ticker):
            continue
        
        if ticker in REDDIT_ONLY_TICKERS:
            continue
        
        if ticker in AMBIGUOUS_TICKERS:
            if context_score is None:
                financial_keyword_count = sum(1 for keyword in FINANCIAL_KEYWORDS 
                                             if keyword in text.lower())
                word_count = len(text.split())
                context_score = financial_keyword_count / max(word_count, 1) * 100
            
            if len(ticker) == 2:
                required_score = 90  
            elif len(ticker) == 3:
                required_score = 60   
            else:
                required_score = 40  
            
            if context_score < required_score:
                continue
        
        tickers.add(ticker)
    
    try:
        global nlp_broadcast
        if nlp_broadcast is not None:
            nlp = nlp_broadcast.value
            doc = nlp(text)

            for ent in doc.ents:
                if ent.label_ == "ORG":
                    ticker = get_ticker_from_company_name(ent.text)
                    if ticker:
                        tickers.add(ticker)
    except Exception:
        pass
    
    return list(tickers)

# Global broadcast variable for SpaCy model
nlp_broadcast = None

class SparkRedditProcessor:
    def __init__(self, max_retries=5):
        self.spark = None
        self.max_retries = max_retries
        self.retry_count = 0
        self.setup_spark()
        
    def setup_spark(self):
        
        self.spark = SparkSession.builder \
            .appName("RedditTickerExtractor") \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.executor.heartbeatInterval", "30s") \
            .config("spark.network.timeout", "300s") \
            .config("spark.executor.heartbeat.maxFailures", "10") \
            .config("spark.sql.streaming.stopGracefullyOnShutdown", "true") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "false") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")

        # Load and broadcast SpaCy model globally
        global nlp_broadcast
        print("📦 Loading SpaCy model...")
        nlp_model = spacy.load("en_core_web_sm")
        nlp_broadcast = self.spark.sparkContext.broadcast(nlp_model)

        print("✅ Spark session created successfully")
        print("✅ SpaCy model broadcasted to workers")

    def cleanup_checkpoint(self):
        """Remove corrupted checkpoint directory"""
        try:
            if os.path.exists(CHECKPOINT_DIR):
                shutil.rmtree(CHECKPOINT_DIR)
                print(f"🧹 Cleaned up checkpoint directory: {CHECKPOINT_DIR}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean checkpoint: {e}")

    def wait_with_backoff(self):
        """Wait with exponential backoff between retries"""
        delay = min(300, 10 * (2 ** self.retry_count))  # Cap at 5 minutes
        print(f"⏳ Waiting {delay}s before retry {self.retry_count + 1}/{self.max_retries}")
        time.sleep(delay)

    def check_kafka_health(self):
        """Basic Kafka connectivity check"""
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                value_serializer=lambda x: x.encode('utf-8'),
                request_timeout_ms=5000
            )
            producer.close()
            return True
        except Exception as e:
            print(f"❌ Kafka health check failed: {e}")
            return False
    
    def get_reddit_data_schema(self):
        return StructType([
            StructField("id", StringType(), True),
            StructField("subreddit", StringType(), True),
            StructField("body", StringType(), True),
            StructField("timestamp", StringType(), True),
            StructField("type", StringType(), True)
        ])
    
    def process_stream(self):
        print("🚀 Starting Spark streaming process...")
        df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
            .option("subscribe", REDDIT_DATA_TOPIC) \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()

        print(f"📖 Reading from Kafka topic: {REDDIT_DATA_TOPIC}")
        
        reddit_schema = self.get_reddit_data_schema()
        
        parsed_df = df.select(
            col("key").cast("string").alias("kafka_key"),
            from_json(col("value").cast("string"), reddit_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select(
            "kafka_key",
            "kafka_timestamp", 
            "data.*"
        )
        
        windowed_df = parsed_df \
            .withWatermark("kafka_timestamp", "2 minutes") \
            .groupBy(
                window(col("kafka_timestamp"), "30 seconds"),
                col("subreddit")
            ) \
            .agg(collect_list(struct("id", "subreddit", "body", "timestamp", "type")).alias("messages"))
        
        processed_df = windowed_df.select(
            col("subreddit").alias("kafka_key"),
            explode(col("messages")).alias("message")
        ).select(
            "kafka_key",
            col("message.id").alias("id"),
            col("message.subreddit").alias("subreddit"), 
            col("message.body").alias("body"),
            col("message.timestamp").alias("timestamp"),
            col("message.type").alias("type")
        ) \
        .withColumn("tickers", udf(extract_tickers_from_text, ArrayType(StringType()))(col("body"))) \
        .withColumn("ticker_count", size(col("tickers"))) \
        .withColumn("processed_timestamp", current_timestamp()) \
        .filter(col("ticker_count") > 0)
        
        output_df = processed_df.select(
            col("subreddit").alias("kafka_key"),
            to_json(struct(
                col("id"),
                col("subreddit"),
                col("body"),
                col("timestamp"),
                col("type"),
                col("tickers"),
                col("ticker_count"),
                col("processed_timestamp").cast("string").alias("processed_timestamp")
            )).alias("value")
        )
        
        query = output_df \
            .writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
            .option("topic", TICKER_MENTIONS_TOPIC) \
            .option("checkpointLocation", CHECKPOINT_DIR) \
            .outputMode("append") \
            .trigger(processingTime="1 minute") \
            .start()
        
        print(f"📝 Writing processed data to: {TICKER_MENTIONS_TOPIC}")
        print("✅ Streaming started successfully!")
        
        try:
            query.awaitTermination()
        except KeyboardInterrupt:
            print("\n⏹️  Stopping Spark streaming...")
            query.stop()
            self.spark.stop()
            print("✅ Spark streaming stopped successfully")
            raise  # Re-raise to prevent retry on manual stop
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            print("🔄 Attempting graceful shutdown...")
            try:
                query.stop()
                self.spark.stop()
            except:
                pass
            raise  # Re-raise for retry logic

    def run_with_auto_restart(self):
        """Main method with auto-restart logic"""
        print(f"🚀 Starting Spark processor with auto-restart (max {self.max_retries} retries)")

        while self.retry_count <= self.max_retries:
            try:
                if self.retry_count > 0:
                    print(f"🔄 Restart attempt {self.retry_count}/{self.max_retries}")

                    # Health checks before restart
                    if not self.check_kafka_health():
                        print("❌ Kafka not available, waiting before retry...")
                        self.wait_with_backoff()
                        self.retry_count += 1
                        continue

                    # Cleanup and reinitialize
                    self.cleanup_checkpoint()
                    self.setup_spark()

                # Start processing
                self.process_stream()
                print("✅ Streaming completed successfully")
                break

            except KeyboardInterrupt:
                print("\n⏹️  Manual stop - no restart")
                break
            except Exception as e:
                self.retry_count += 1
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"❌ [{timestamp}] Attempt {self.retry_count} failed: {e}")

                if self.retry_count <= self.max_retries:
                    self.wait_with_backoff()
                else:
                    print(f"💥 Max retries ({self.max_retries}) exceeded. Giving up.")
                    print("💡 Check logs, Kafka connectivity, and system resources")
                    break

def main():
    processor = SparkRedditProcessor()
    processor.run_with_auto_restart()

if __name__ == "__main__":
    main()