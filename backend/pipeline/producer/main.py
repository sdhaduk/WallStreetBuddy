import json
import os
import threading
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
import praw
from kafka import KafkaProducer

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output for Docker logs
    ]
)
logger = logging.getLogger(__name__)

# Reddit configuration
reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
reddit_client_agent = os.getenv("REDDIT_CLIENT_AGENT")

logger.info("🚀 Starting Reddit Kafka Producer")
logger.info(f"Reddit User Agent: {reddit_client_agent}")

if not all([reddit_client_id, reddit_client_secret, reddit_client_agent]):
    logger.error("❌ Missing Reddit API credentials. Check environment variables.")
    raise ValueError("Reddit API credentials not found")

try:
    reddit = praw.Reddit(
        client_id=reddit_client_id,
        client_secret=reddit_client_secret,
        user_agent=reddit_client_agent,
    )
    logger.info("✅ Reddit API connection established")
except Exception as e:
    logger.error(f"❌ Failed to connect to Reddit API: {e}")
    raise

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
REDDIT_DATA_TOPIC = 'reddit-data'
TICKER_MENTIONS_TOPIC = 'ticker-mentions'

logger.info(f"Kafka servers: {KAFKA_BOOTSTRAP_SERVERS}")
logger.info(f"Target topic: {REDDIT_DATA_TOPIC}")

class RedditKafkaProducer:
    def __init__(self):
        logger.info("🔗 Initializing Kafka producer...")
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=3,
                retry_backoff_ms=1000
            )
            logger.info("✅ Kafka producer initialized successfully")
            self.message_count = 0
            self.error_count = 0
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kafka producer: {e}")
            raise
    
    def create_comment_message(self, comment):
        """Convert Reddit comment to Kafka message format"""
        return {
            'id': comment.id,
            'subreddit': str(comment.subreddit),
            'body': comment.body,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'comment'
        }
    
    def create_submission_message(self, submission):
        """Convert Reddit submission to Kafka message format"""
        return {
            'id': submission.id,
            'subreddit': str(submission.subreddit),
            'body': submission.title + submission.selftext,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'submission'
        }
    
    def stream_comments_to_kafka(self, subreddits):
        """Stream Reddit comments to Kafka"""
        subreddit = reddit.subreddit(subreddits)
        print(f"Starting comment stream for: {subreddits}")
        
        for comment in subreddit.stream.comments(skip_existing=True):
            try:
                message = self.create_comment_message(comment)
                
                # Use subreddit as key for partitioning
                key = str(comment.subreddit)
                
                self.producer.send(
                    REDDIT_DATA_TOPIC,
                    key=key,
                    value=message
                )
                

            except Exception as e:
                logger.error(f"❌ Error processing comment: {e}")
    
    def stream_submissions_to_kafka(self, subreddits):
        """Stream Reddit submissions to Kafka"""
        subreddit = reddit.subreddit(subreddits)
        logger.info(f"📡 Starting submission stream for: {subreddits}")
        
        for submission in subreddit.stream.submissions(skip_existing=True):
            try:
                message = self.create_submission_message(submission)
                
                # Use subreddit as key for partitioning
                key = str(submission.subreddit)
                
                self.producer.send(
                    REDDIT_DATA_TOPIC,
                    key=key,
                    value=message
                )
                
            except Exception as e:
                logger.error(f"❌ Error processing submission: {e}")
    
    def close(self):
        """Close the Kafka producer"""
        self.producer.close()

def main():
    # Subreddits to monitor
    subreddits = "stocks+wallstreetbets+ValueInvesting"
    
    # Create producer instance
    producer = RedditKafkaProducer()
    
    try:
        print("Starting Reddit to Kafka streams...")
        
        # Create threads for both streams
        
        comment_thread = threading.Thread(
            target=producer.stream_comments_to_kafka,
            args=(subreddits,),
            daemon=True
        )
        submission_thread = threading.Thread(
            target=producer.stream_submissions_to_kafka,
            args=(subreddits,),
            daemon=True
        )
        
        # Start both threads
        comment_thread.start()
        submission_thread.start()
        
        print("Both streams started. Press Ctrl+C to stop.")
        
        # Keep main thread alive
        comment_thread.join()
        submission_thread.join()
        
    except KeyboardInterrupt:
        print("\nStopping streams...")
    finally:
        producer.close()

if __name__ == "__main__":
    main()