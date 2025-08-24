import json
from kafka import KafkaConsumer

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
REDDIT_DATA_TOPIC = 'reddit-data'
TICKER_MENTIONS_TOPIC = 'ticker-mentions'

class RedditKafkaConsumer:
    def __init__(self):
        self.running = True
    
    def create_consumer(self, topics, group_id):
        """Create a Kafka consumer for specified topics"""
        return KafkaConsumer(
            *topics,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='latest',  # Start from latest messages
            enable_auto_commit=True
        )
    
    def consume_ticker_mentions(self):
        """Consume and display processed ticker mentions from Spark"""
        consumer = self.create_consumer([TICKER_MENTIONS_TOPIC], 'ticker-mentions-group')
        
        print(f"Started consuming processed data from topic: {TICKER_MENTIONS_TOPIC}")
        print("Waiting for Spark to process Reddit data...")
        
        try:
            for message in consumer:
                if not self.running:
                    break
                
                data = message.value
                print(f"[SPARK PROCESSED {data['type'].upper()}] r/{data['subreddit']}")
                print(f"  ID: {data['id']}")
                print(f"  Body: {data['body']}")
                print(f"  Original Time: {data['timestamp']}")
                print(f"  Processed: {data['processed']}")
                print(f"  Processed Time: {data['processed_timestamp']}")
                print(f"  Type: {data['type']}")
                print("=" * 60)
                
        except Exception as e:
            print(f"Error in ticker mentions consumer: {e}")
        finally:
            consumer.close()
    
    def stop(self):
        """Stop all consumers"""
        self.running = False

def main():
    # Create consumer instance
    consumer = RedditKafkaConsumer()
    
    try:
        print("Starting Ticker Mentions consumer (testing Spark pipeline)...")
        
        # Start ticker mentions consumer to test Spark processing
        consumer.consume_ticker_mentions()
        
    except KeyboardInterrupt:
        print("\nStopping consumer...")
        consumer.stop()

if __name__ == "__main__":
    main()