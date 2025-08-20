# WallStreetBuddy - Personal Project Design

## Executive Summary

WallStreetBuddy is a personal analytics project that monitors r/wallstreetbets for stock ticker mentions, providing insights through automated analysis and market data. The system processes social media data in 3-day windows to identify trending stocks in a simple, maintainable way.

## System Architecture

### Simplified Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Reddit API    │───▶│   Data Pipeline │───▶│   Elasticsearch │
│   (r/wsb)       │    │   (Kafka + NLP) │    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ External APIs   │◀───│  Batch Enricher │◀───│   Flask API     │
│(Yahoo, OpenAI)  │    │   (3-day cycle) │    │   (Simple REST) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                               ┌─────────────────┐
                               │  React Frontend │
                               │  (Dashboard)    │
                               └─────────────────┘
```

**Why this simplified approach?**
- Removed Redis dependency (Kafka provides durability)
- Simplified API layer (Flask is sufficient for personal use)
- Combined enrichment into single service
- Maintains core functionality with fewer moving parts

## Component Specifications

### 1. Data Ingestion Layer

#### Reddit Stream Processor
**Technology**: Python + PRAW
**Function**: Continuous Reddit data ingestion
```python
# Core functionality
class RedditStreamer:
    def __init__(self):
        self.reddit = praw.Reddit(...)
        self.producer = KafkaProducer(...)
    
    def stream_subreddit(self, subreddit_name="wallstreetbets"):
        # Stream posts and comments continuously
        # Send to Kafka topic: 'raw_reddit'
```

**Configuration**:
- Rate limiting: 600 requests/10 minutes (Reddit API limit)
- Retry mechanism: Exponential backoff
- Health monitoring: Heartbeat every 30 seconds

### 2. Stream Processing Pipeline

#### NLP Processing Service
**Technology**: Python + spaCy + Kafka Consumer
**Function**: Extract and validate stock tickers from text

**Personal Project Approach**: Using simple Kafka consumers with basic error handling - sufficient for personal use.

```python
class TickerExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.ticker_symbols = self.load_ticker_symbols()
    
    def extract_tickers(self, text):
        # NLP processing + ticker validation
        # Enhanced regex patterns for $AAPL, AAPL, etc.
        return validated_tickers
```

**Optimizations Added**:
- Pre-compiled regex patterns for better performance
- Ticker symbol whitelist/blacklist management
- Context-aware filtering (avoid false positives like "US", "IT")

### 3. Real-time Analytics Engine

#### Windowed Aggregation Service
**Technology**: Python + Kafka Consumer + In-Memory Dict
**Function**: 3-day sliding window ticker counting

**Personal Project Approach**: Simple in-memory counting with periodic Elasticsearch saves for persistence - no Redis needed for personal scale.

```python
class WindowedCounter:
    def __init__(self):
        self.ticker_counts = defaultdict(int)
        self.window_size = timedelta(days=3)
        self.window_start = datetime.now()
    
    def update_counts(self, ticker, timestamp):
        # Simple in-memory counting
        # Reset window every 3 days
        if self._should_reset_window(timestamp):
            self._finalize_and_reset()
        self.ticker_counts[ticker] += 1
```

### 4. Data Enrichment Pipeline

#### Stock Data Enricher
**Technology**: Python + yfinance + OpenAI API
**Function**: Enrich top 10 tickers with financial data and AI analysis

**Personal Project Approach**: Simple batch processing every 3 days with basic error handling - no complex caching needed.

```python
class StockEnricher:
    def __init__(self):
        self.yahoo_client = yfinance
        self.openai_client = OpenAI(...)
    
    def enrich_batch(self, top_tickers):
        # Simple sequential processing
        # Called only every 3 days for top 10
        enriched_data = []
        for ticker in top_tickers:
            stock_data = self._get_stock_data(ticker)
            ai_analysis = self._get_ai_analysis(ticker)
            enriched_data.append({
                'ticker': ticker,
                'stock_data': stock_data,
                'analysis': ai_analysis
            })
        return enriched_data
```

### 5. Data Storage Layer

#### Elasticsearch Configuration
**Indices Structure**:
```json
{
  "wsb_batches": {
    "mappings": {
      "properties": {
        "batch_id": {"type": "keyword"},
        "window_start": {"type": "date"},
        "window_end": {"type": "date"},
        "top_tickers": {
          "type": "nested",
          "properties": {
            "symbol": {"type": "keyword"},
            "mention_count": {"type": "integer"},
            "stock_data": {"type": "object"},
            "ai_analysis": {"type": "text"}
          }
        }
      }
    }
  },
  "wsb_current": {
    "mappings": {
      "properties": {
        "timestamp": {"type": "date"},
        "ticker_counts": {"type": "object"}
      }
    }
  }
}
```

### 6. API Gateway

#### Flask API Service
**Technology**: Flask + Flask-CORS
**Function**: Simple RESTful API

**Personal Project Choice**: Sticking with Flask as originally planned - simpler setup, fewer dependencies, perfectly adequate for personal use.

```python
# Simple Flask API Endpoints
@app.route("/api/top10/current")
def get_current_top10():
    # Returns real-time top 10 in progress
    return jsonify(es_client.get_current_batch())

@app.route("/api/top10/latest")
def get_latest_batch():
    # Returns most recent completed batch
    return jsonify(es_client.get_latest_batch())

@app.route("/api/top10/<batch_id>")
def get_batch(batch_id):
    # Returns specific historical batch
    return jsonify(es_client.get_batch(batch_id))
```

### 7. Frontend Application

#### React Dashboard
**Technology**: React 18 + Typescript + Vite
**UI Framework**: shadcn/ui + Tailwind CSS
**Charts**: Recharts
**State Management**: useState + useEffect


```tsx
// Key Components
const Dashboard = () => {
  const [currentTop10, setCurrentTop10] = useState([]);
  const [latestBatch, setLatestBatch] = useState(null);

  useEffect(() => {
    // Simple polling every 30 seconds
    const interval = setInterval(() => {
      fetch('/api/top10/current')
        .then(res => res.json())
        .then(data => setCurrentTop10(data));
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);
};
```

## Simple Deployment

### Docker Compose Setup
```yaml
# Simple docker-compose.yml for personal use
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
  
  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on: [zookeeper]
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
  
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
  
  app:
    build: .
    depends_on: [kafka, elasticsearch]
    volumes:
      - .:/app
    environment:
      - REDDIT_CLIENT_ID=${REDDIT_CLIENT_ID}
      - REDDIT_CLIENT_SECRET=${REDDIT_CLIENT_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
  
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [app]
```

**Why this simplified approach?**
- Single Python app container instead of microservices
- All services run in one container for easier management
- Fewer dependencies and simpler debugging
- Perfect for personal development and learning

### Simple Monitoring

#### Basic Logging
- **Python Logging**: Standard library with file rotation
- **Console Output**: Debug information during development
- **Error Tracking**: Simple file-based error logs

#### Key Health Checks
- Reddit API connection status
- Kafka topic health
- Elasticsearch connectivity
- Basic performance metrics in logs

**Why simple monitoring?**
- For personal projects, complex monitoring is overkill
- Console logs and simple files are easier to debug
- Can always add more sophisticated monitoring later if needed

## Basic Security

### API Protection
- CORS enabled for frontend
- Basic input validation
- Environment variables for API keys
- No authentication needed (personal use only)

### Data Handling
- Public Reddit data only
- No personal information stored
- API keys in environment variables (.env file)

**Personal Project Security:**
- Focus on protecting API keys
- Basic validation to prevent crashes
- No need for enterprise-level security measures

## Performance Expectations

### Realistic Personal Project Goals
- Reddit ingestion: Handle typical r/wsb volume (50-200 posts/hour)
- NLP processing: Process messages as they come
- API response: Fast enough for dashboard updates
- Frontend: Responsive on personal machine

**Performance Philosophy for Personal Projects:**
- "Good enough" is perfect
- Optimize only if there are actual problems
- Focus on functionality over performance metrics

## Cost Management

### Free/Low-Cost Approach
- **Reddit API**: Free with rate limits
- **Yahoo Finance**: Free tier sufficient
- **OpenAI API**: Minimal usage (10 calls every 3 days)
- **Infrastructure**: Run locally or on cheap VPS

**Cost Philosophy:**
- Keep API calls to minimum
- Use free tiers where possible
- Optimize for learning, not cost efficiency

## Simple Development Setup

### Getting Started
```bash
# Clone and setup
git clone <repo>
cd wallstreetbuddy

# Setup environment
cp .env.example .env
# Add your API keys to .env

# Start with Docker
docker-compose up -d

# Or run locally
pip install -r requirements.txt
python src/main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Development Philosophy
- Keep it simple
- Manual testing is fine
- Add complexity only when needed
- Focus on making it work first

## Database Schema

### Elasticsearch Document Examples

#### Completed Batch Document
```json
{
  "batch_id": "batch_2024_01_15_001",
  "window_start": "2024-01-12T00:00:00Z",
  "window_end": "2024-01-15T00:00:00Z",
  "created_at": "2024-01-15T00:30:00Z",
  "total_mentions": 15420,
  "total_posts_analyzed": 2341,
  "top_tickers": [
    {
      "symbol": "AAPL",
      "mention_count": 1250,
      "sentiment_score": 0.65,
      "stock_data": {
        "current_price": 192.53,
        "change_percent": 2.3,
        "volume": 50231400,
        "market_cap": 3010000000000
      },
      "ai_analysis": "Apple shows strong bullish sentiment...",
      "price_trend": "bullish"
    }
  ]
}
```

#### Current Window Document
```json
{
  "window_id": "current_2024_01_16",
  "window_start": "2024-01-13T00:00:00Z",
  "last_updated": "2024-01-16T10:30:00Z",
  "ticker_counts": {
    "AAPL": 890,
    "TSLA": 720,
    "NVDA": 650
  },
  "total_mentions": 8430,
  "posts_analyzed": 1205
}
```

## Error Handling & Recovery

### Failure Scenarios
1. **Reddit API Downtime**: Graceful degradation, resume from last checkpoint
2. **Kafka Broker Failure**: Automatic failover, data replication
3. **Elasticsearch Outage**: Circuit breaker pattern, fallback to cache
4. **External API Rate Limits**: Exponential backoff, request queuing

### Data Consistency
- **At-least-once delivery** for critical data
- **Idempotent processing** for all services
- **Checkpoint mechanism** for window state recovery

## Future Enhancements

### Phase 2 Features
- Multi-subreddit support (r/investing, r/stocks)
- Historical trend analysis and comparison
- Real-time sentiment tracking
- Mobile application

### Phase 3 Features
- Machine learning models for price prediction
- Social trading signals
- User accounts and watchlists
- Advanced analytics dashboard

## Simple Implementation Plan

### Phase 1: Basic Pipeline (Weekend 1-2)
- Get Reddit data flowing to Kafka
- Basic ticker extraction with spaCy
- Simple counting in memory

### Phase 2: Storage & Enrichment (Weekend 3-4)
- Save data to Elasticsearch
- Add Yahoo Finance integration
- Basic OpenAI analysis

### Phase 3: API & Frontend (Weekend 5-6)
- Simple Flask API
- Basic React dashboard
- Data visualization with charts

### Phase 4: Polish & Deploy (Weekend 7-8)
- Docker setup
- Bug fixes and improvements
- Deploy locally or to VPS

**Personal Project Approach:**
- Work on weekends/free time
- Get MVP working quickly
- Iterate and improve gradually

---

## Summary of Personal Project Simplifications

**Maintained Core Architecture:**
- Your original design was excellent for the core pipeline
- Kafka for messaging reliability 
- Elasticsearch for data storage and analytics
- React frontend with modern charting

**Simplified for Personal Use:**

1. **Single App Container**: Combined microservices into one Python app for easier management
2. **Removed Redis**: Kafka provides sufficient durability, in-memory counting is fine  
3. **Kept Flask**: Simpler than FastAPI for personal projects, fewer dependencies
4. **JavaScript over TypeScript**: Less complexity, faster development for personal use
5. **Basic Monitoring**: Simple logging instead of enterprise monitoring stack
6. **Minimal Security**: Focus on API key protection, no auth needed
7. **Local/VPS Deployment**: No need for cloud orchestration
8. **Simple Error Handling**: Basic try/catch, restart on failure

**Why These Changes Work for Personal Projects:**
- Faster to develop and debug
- Fewer dependencies to manage  
- Still maintains core functionality
- Easy to enhance later if needed
- Perfect for learning and experimentation

The simplified design keeps all your smart architectural decisions while removing enterprise complexity that isn't needed for personal use.