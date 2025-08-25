import re
from typing import List
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_json, struct, current_timestamp, window, 
    udf, collect_list, explode, size
)
from pyspark.sql.types import StructType, StructField, StringType, ArrayType
import spacy
from ticker.ticker_manager import is_valid_ticker, get_ticker_from_company_name

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
REDDIT_DATA_TOPIC = "reddit-data"
TICKER_MENTIONS_TOPIC = "ticker-mentions"
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
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        
        for ent in doc.ents:
            if ent.label_ == "ORG":
                ticker = get_ticker_from_company_name(ent.text)
                if ticker:
                    tickers.add(ticker)
    except Exception as e:
        pass
    
    return list(tickers)

extract_tickers_udf = udf(extract_tickers_from_text, ArrayType(StringType()))

class SparkRedditProcessor:
    def __init__(self):
        self.spark = None
        self.setup_spark()
        
    def setup_spark(self):
        
        self.spark = SparkSession.builder \
            .appName("RedditTickerExtractor") \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        
        print("✅ Spark session created successfully")
    
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
                window(col("kafka_timestamp"), "10 minutes"),
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
        .withColumn("tickers", extract_tickers_udf(col("body"))) \
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
            .option("checkpointLocation", "/tmp/spark-checkpoint-new") \
            .outputMode("append") \
            .trigger(processingTime="1 minute") \
            .start()
        
        print(f"📝 Writing processed data to: {TICKER_MENTIONS_TOPIC}")
        print("✅ Streaming started successfully!")
        print("📊 Processing Reddit data in 10-minute batches with ticker extraction")
        print("Press Ctrl+C to stop the stream")
        
        try:
            query.awaitTermination()
        except KeyboardInterrupt:
            print("\n⏹️  Stopping Spark streaming...")
            query.stop()
            self.spark.stop()
            print("✅ Spark streaming stopped successfully")

def main():
    processor = SparkRedditProcessor()
    processor.process_stream()

if __name__ == "__main__":
    main()