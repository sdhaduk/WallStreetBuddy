"""
Scheduled job definitions for WallStreetBuddy
"""
import logging
import httpx
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch

from ..config import settings

logger = logging.getLogger(__name__)


async def stock_analysis_job():
    """
    Scheduled job to generate analysis reports for top 10 tickers from latest batch
    Runs every 3 days at 12:15 AM (15 minutes after home batch data job)

    Makes HTTP request to existing /api/analysis/generate-batch endpoint
    """
    job_start_time = datetime.now()
    logger.info(f"🚀 Starting scheduled stock analysis job at {job_start_time}")

    try:
        # Make HTTP POST request to the existing endpoint
        base_url = "http://fast-api:8000"
        endpoint_url = f"{base_url}{settings.api_prefix}/analysis/generate-batch"

        timeout = httpx.Timeout(1500.0)  # 25 minute timeout for AI generation (2.5 mins per report)

        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"📡 Making request to {endpoint_url}")

            # Add internal API key header for security
            headers = {"X-Internal-API-Key": settings.internal_api_key}
            response = await client.post(endpoint_url, headers=headers)
            response.raise_for_status()

            result = response.json()

            job_duration = datetime.now() - job_start_time
            logger.info(
                f"✅ Scheduled stock analysis job completed in {job_duration.total_seconds():.2f}s"
            )
            logger.info(f"📊 Result: {result}")

            return result

    except httpx.TimeoutException:
        job_duration = datetime.now() - job_start_time
        logger.error(f"⏰ Scheduled stock analysis job timed out after {job_duration.total_seconds():.2f}s")
        raise

    except httpx.HTTPStatusError as e:
        job_duration = datetime.now() - job_start_time
        logger.error(
            f"❌ Scheduled stock analysis job failed with HTTP {e.response.status_code} "
            f"after {job_duration.total_seconds():.2f}s: {e.response.text}"
        )
        raise

    except Exception as e:
        job_duration = datetime.now() - job_start_time
        logger.error(f"❌ Scheduled stock analysis job failed after {job_duration.total_seconds():.2f}s: {e}")
        raise


async def home_batch_data_job():
    """
    Scheduled job to calculate and store 3-day batch data for home page
    Runs every 3 days at 12:00 AM (5 minutes before analysis job)

    Calculates completed 3-day batch period and stores results in Elasticsearch
    """
    job_start_time = datetime.now()
    logger.info(f"🏠 Starting home batch data job at {job_start_time}")

    try:
        # Query for completed 3-day batch (4 days ago to 1 day ago)
        query = {
            "range": {
                "@timestamp": {
                    "gte": "now-4d/d",  # Start 4 days ago at start of day
                    "lt": "now-1d/d"    # End 1 day ago at start of day (exclusive)
                }
            }
        }

        batch_id = f"batch-{datetime.now().strftime('%Y-%m-%d')}"
        logger.info(f"📊 Calculating batch: {batch_id} (now-4d/d to now-1d/d)")

        # Connect to Elasticsearch
        es = Elasticsearch([settings.elasticsearch_url])

        # Aggregate top 10 tickers for this batch
        resp = es.search(
            index="ticker-mentions-*",
            size=0,
            track_total_hits=True,  # Enable accurate total count beyond 10K limit
            query=query,
            aggregations={
                "ticker_mentions": {
                    "terms": {
                        "field": "tickers",
                        "size": 10,
                        "order": {"_count": "desc"}
                    }
                }
            }
        )

        data = resp.body
        buckets = data.get("aggregations", {}).get("ticker_mentions", {}).get("buckets", [])

        # Get total mentions count
        total_mentions = data.get("hits", {}).get("total", {})
        if isinstance(total_mentions, dict):
            total_mentions_count = total_mentions.get("value", 0)
        else:
            total_mentions_count = total_mentions or 0

        # Format top tickers data
        top_tickers = []
        for bucket in buckets:
            top_tickers.append({
                "ticker": bucket["key"],
                "mentions": bucket["doc_count"]
            })

        logger.info(f"📈 Found {len(top_tickers)} tickers with {total_mentions_count} total mentions")

        # Calculate actual date range that matches the query
        now = datetime.now()
        # "now-4d/d" = 4 days ago at start of day
        batch_start = (now - timedelta(days=4)).replace(hour=0, minute=0, second=0, microsecond=0)
        # "now-1d/d" = 1 day ago at start of day (exclusive), so actual end is 2 days ago at end of day
        batch_end = (now - timedelta(days=2)).replace(hour=23, minute=59, second=59, microsecond=999999)

        # Create batch document that matches template exactly
        batch_doc = {
            "@timestamp": now.isoformat(),
            "batch_id": batch_id,
            "batch_start": batch_start.isoformat(),
            "batch_end": batch_end.isoformat(),
            "top_tickers": top_tickers,
            "total_mentions": total_mentions_count,
            "total_posts": total_mentions_count,
            "status": "completed"
        }

        # Store in Elasticsearch with date-based index
        index_name = f"home-batch-{now.strftime('%Y.%m.%d')}"

        result = es.index(
            index=index_name,
            document=batch_doc,
            id=batch_id  # Use batch_id as document ID for easy retrieval
        )

        job_duration = datetime.now() - job_start_time
        logger.info(f"✅ Home batch data job completed in {job_duration.total_seconds():.2f}s")
        logger.info(f"📂 Stored batch {batch_id} in index {index_name}")
        logger.info(f"🎯 Top tickers: {[t['ticker'] for t in top_tickers]}")

        return {
            "status": "completed",
            "batch_id": batch_id,
            "top_tickers_count": len(top_tickers),
            "total_mentions": total_mentions_count,
            "index_name": index_name,
            "duration_seconds": job_duration.total_seconds()
        }

    except Exception as e:
        job_duration = datetime.now() - job_start_time
        logger.error(f"❌ Home batch data job failed after {job_duration.total_seconds():.2f}s: {e}")
        raise