# Reddit Kafka Streaming Pipeline

A real-time data pipeline that streams Reddit comments and submissions to Kafka for processing.

## Setup

### 1. Install Dependencies
```bash
uv pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file with your Reddit API credentials:
```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_CLIENT_AGENT=your_user_agent
```

### 3. Start Kafka Infrastructure
```bash
# Start Kafka and Zookeeper
docker-compose up -d

# Wait for services to be ready (30-60 seconds)
# Check status
docker-compose ps
```

### 4. Create Kafka Topics
```bash
python setup_kafka.py
```

## Usage

### Start the Pipeline

**Terminal 1 - Producer (Reddit → Kafka):**
```bash
python kafka_producer.py
```

**Terminal 2 - Consumer (Kafka → Processing):**
```bash
python kafka_consumer.py
```

### Monitor with Kafka UI
Visit http://localhost:8080 to see:
- Topic metrics
- Message throughput
- Consumer lag
- Live message data

## Architecture

```
Reddit API → Producer → Kafka Topics → Consumer → Processing
                        ├─ reddit-comments
                        └─ reddit-submissions
```

### Topics
- **reddit-comments**: Real-time Reddit comments
- **reddit-submissions**: New Reddit posts/submissions

### Subreddits Monitored
- r/stocks
- r/wallstreetbets  
- r/ValueInvesting
- r/investing

## Data Format

### Comment Message
```json
{
  "id": "comment_id",
  "subreddit": "stocks",
  "author": "username", 
  "body": "comment text",
  "score": 10,
  "created_utc": 1234567890,
  "timestamp": "2024-01-01T12:00:00",
  "permalink": "https://reddit.com/...",
  "type": "comment"
}
```

### Submission Message
```json
{
  "id": "submission_id",
  "subreddit": "stocks",
  "author": "username",
  "title": "post title",
  "selftext": "post body",
  "url": "https://...",
  "score": 100,
  "upvote_ratio": 0.95,
  "num_comments": 25,
  "created_utc": 1234567890,
  "timestamp": "2024-01-01T12:00:00", 
  "permalink": "https://reddit.com/...",
  "type": "submission"
}
```

## Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (optional - deletes all data)
docker-compose down -v
```