# WallStreetBuddy Backend

Four deployable services plus the infrastructure config and scripts that support them.
All commands below are run from this `backend/` directory.

## Directory map

```
backend/
├── api/            FastAPI service + background scheduler (one image, shared config)
│   ├── main.py         FastAPI app entrypoint
│   ├── config.py       Pydantic settings (reads .env)
│   ├── routers/        HTTP endpoints (health, ticker, analysis)
│   ├── agent/          pydantic-ai stock researcher agent and its Yahoo Finance tools
│   └── scheduler/      APScheduler service, job definitions, standalone entrypoint
├── pipeline/       Streaming services + shared ticker library
│   ├── producer/       Reddit → Kafka producer
│   ├── processor/      Spark Structured Streaming ticker extractor
│   └── ticker/         TickerManager (SEC ticker lookup); data/ holds the
│                       static manual mapping and the runtime SEC cache
├── logstash/       Logstash config mounted by docker-compose (Kafka → Elasticsearch)
├── scripts/        One-off local-dev utilities (Kafka topics, ES templates, ticker refresh)
├── docker/         One Dockerfile per image (build context is backend/)
├── requirements/   One requirements file per image, plus dev.txt for the local venv
└── docker-compose.yml
```

Kubernetes manifests for the whole cluster (frontend, backend, Kafka, Elasticsearch,
Logstash) live at the repo root in `deploy/k8s/`.

## Services

| Service          | Local run                              | Image / Dockerfile                    | Requirements                       |
|------------------|----------------------------------------|---------------------------------------|------------------------------------|
| API              | `uvicorn api.main:app --reload`        | `docker/api.Dockerfile`               | `requirements/api.txt`             |
| Scheduler        | `python -m api.scheduler.main`         | same image as API, different command  | `requirements/api.txt`             |
| Kafka producer   | `python -m pipeline.producer.main`     | `docker/kafka-producer.Dockerfile`    | `requirements/kafka-producer.txt`  |
| Spark processor  | `python -m pipeline.processor.main`    | `docker/spark-processor.Dockerfile`   | `requirements/spark-processor.txt` |

The scheduler runs inside the API process by default; set `DISABLE_SCHEDULER=true` to run
the API alone and deploy the scheduler as its own process (see `deploy/k8s/scheduler.yaml`).

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt          # union of all service requirements
cp .env.example .env                          # or create .env with the keys below

docker compose up -d zookeeper kafka kafka-ui elasticsearch logstash
python scripts/setup_kafka.py                 # create topics
python scripts/setup_elasticsearch.py         # create ILM policies + index templates
```

Then start any of the services from the table above, or bring up everything with
`docker compose up --build`.

Environment variables read by the services: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`,
`REDDIT_CLIENT_AGENT`, `KAFKA_BOOTSTRAP_SERVERS`, `ELASTICSEARCH_URL`, `OPENAI_API_KEY`,
`INTERNAL_API_KEY`, `STOCK_ANALYSIS_SYSTEM_PROMPT`.

## Building images

```bash
docker build -f docker/api.Dockerfile             -t fast-api .
docker build -f docker/kafka-producer.Dockerfile  -t kafka-producer .
docker build -f docker/spark-processor.Dockerfile -t spark-processor .
```
