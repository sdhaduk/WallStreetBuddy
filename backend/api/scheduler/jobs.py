"""
Scheduled job definitions for WallStreetBuddy
"""
import asyncio
import logging
import httpx
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError
from typing import Dict, Any, List

from ..config import settings

logger = logging.getLogger(__name__)

# Global cache for failed results during ES outages
failed_results_cache: List[Dict[str, Any]] = []

# Retry configuration for job-level operations
MAX_STORAGE_ATTEMPTS = 5
INITIAL_STORAGE_BACKOFF = 30  # seconds
MAX_STORAGE_BACKOFF = 600     # 10 minutes
STORAGE_BACKOFF_MULTIPLIER = 2


async def store_to_elasticsearch_with_retry(index: str, document: Dict[str, Any], doc_id: str = None) -> bool:
    """Store document to Elasticsearch with exponential backoff retry"""
    attempt = 1
    delay = INITIAL_STORAGE_BACKOFF

    while attempt <= MAX_STORAGE_ATTEMPTS:
        try:
            logger.info(f"📀 Attempting Elasticsearch storage (attempt {attempt}/{MAX_STORAGE_ATTEMPTS})")
            es = Elasticsearch([settings.elasticsearch_url])

            if doc_id:
                result = es.index(index=index, document=document, id=doc_id)
            else:
                result = es.index(index=index, document=document)

            logger.info(f"✅ Successfully stored document to {index}")
            return True

        except (ESConnectionError, Exception) as e:
            logger.warning(f"⚠️ Elasticsearch storage failed (attempt {attempt}/{MAX_STORAGE_ATTEMPTS}): {e}")

            if attempt == MAX_STORAGE_ATTEMPTS:
                logger.error(f"❌ Failed to store to Elasticsearch after {MAX_STORAGE_ATTEMPTS} attempts")
                return False

            logger.info(f"⏳ Retrying storage in {delay} seconds...")
            await asyncio.sleep(delay)

            delay = min(delay * STORAGE_BACKOFF_MULTIPLIER, MAX_STORAGE_BACKOFF)
            attempt += 1

    return False


def cache_failed_result(job_type: str, data: Dict[str, Any]):
    cached_result = {
        "job_type": job_type,
        "data": data,
        "cached_at": datetime.now().isoformat(),
        "retry_count": 0
    }
    failed_results_cache.append(cached_result)
    logger.info(f"💾 Cached {job_type} result for later retry (cache size: {len(failed_results_cache)})")


async def process_cached_results():
    """
    Background task to process cached failed results
    Attempts to store cached results when Elasticsearch becomes available
    """
    if not failed_results_cache:
        return

    logger.info(f"🔄 Processing {len(failed_results_cache)} cached results...")
    results_to_retry = failed_results_cache.copy()
    failed_results_cache.clear()

    for cached_result in results_to_retry:
        try:
            job_type = cached_result["job_type"]
            data = cached_result["data"]
            cached_at = cached_result["cached_at"]

            logger.info(f"🔄 Attempting to store cached {job_type} result from {cached_at}")

            if job_type == "home_batch":
                index_name = data["index_name"]
                doc_id = data.get("batch_id")
                success = await store_to_elasticsearch_with_retry(index_name, data, doc_id)

            elif job_type == "analysis":
                index_name = data["index_name"]
                clean_data = {k: v for k, v in data.items() if k != "index_name"}
                success = await store_to_elasticsearch_with_retry(index_name, clean_data)

            else:
                logger.error(f"❌ Unknown cached job type: {job_type}")
                continue

            if success:
                logger.info(f"✅ Successfully processed cached {job_type} result")

            else:
                cached_result["retry_count"] += 1
                
                if cached_result["retry_count"] < 3:
                    failed_results_cache.append(cached_result)
                    logger.warning(f"⚠️ Re-cached {job_type} result (retry #{cached_result['retry_count']})")

                else:
                    logger.error(f"❌ Dropping {job_type} result after 3 cache retry attempts")

        except Exception as e:
            logger.error(f"❌ Error processing cached result: {e}")
            cached_result["retry_count"] += 1
            if cached_result["retry_count"] < 3:
                failed_results_cache.append(cached_result)


async def stock_analysis_job():
    """
    Scheduled job to generate analysis reports for top 10 tickers from latest batch
    Runs every 3 days at 12:15 AM (15 minutes after home batch data job)

    Makes HTTP request to existing /api/analysis/generate-batch endpoint
    """
    job_start_time = datetime.now()
    logger.info(f"🚀 Starting scheduled stock analysis job at {job_start_time}")

    try:
        await process_cached_results()
        base_url = "http://fast-api:8000"
        endpoint_url = f"{base_url}{settings.api_prefix}/analysis/generate-batch"

        timeout = httpx.Timeout(1500.0)  # 25 minute timeout for AI generation (2.5 mins per report)

        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"📡 Making request to {endpoint_url}")

            headers = {"X-Internal-API-Key": settings.internal_api_key}
            response = await client.post(endpoint_url, headers=headers)
            response.raise_for_status()

            result = response.json()

            # Handle failed reports from the enhanced response structure
            failed_reports = result.get("failed_reports", [])
            if failed_reports:
                failed_report_data = result.get("failed_report_data", {})
                generation_time = result.get("generation_time")
                logger.info(f"💾 Caching {len(failed_reports)} failed reports from analysis batch")

                # Cache each failed report individually for retry
                for ticker in failed_reports:
                    if ticker in failed_report_data:
                        doc = {
                            "@timestamp": generation_time,
                            "ticker": ticker.upper(),
                            "generation_time": generation_time,
                            "report_content": failed_report_data[ticker],
                            "status": "completed",
                            "model_used": "gpt-5",
                        }
                        cached_data = doc.copy()
                        cached_data["index_name"] = result.get("index_name")
                        cache_failed_result("analysis", cached_data)

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
        await process_cached_results()

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

        es = Elasticsearch([settings.elasticsearch_url])
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

        total_mentions = data.get("hits", {}).get("total", {})
        if isinstance(total_mentions, dict):
            total_mentions_count = total_mentions.get("value", 0)
        else:
            total_mentions_count = total_mentions or 0

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

        index_name = f"home-batch-{now.strftime('%Y.%m.%d')}"

        batch_doc = {
            "@timestamp": now.isoformat(),
            "batch_id": batch_id,
            "batch_start": batch_start.isoformat(),
            "batch_end": batch_end.isoformat(),
            "top_tickers": top_tickers,
            "total_mentions": total_mentions_count,
            "total_posts": total_mentions_count,
            "status": "completed",
            "index_name": index_name  # Add for caching
        }

        logger.info(f"💾 Attempting to store batch data to {index_name}")
        storage_success = await store_to_elasticsearch_with_retry(index_name, batch_doc, batch_id)

        if storage_success:
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
        else:
            cache_failed_result("home_batch", batch_doc)
            job_duration = datetime.now() - job_start_time

            logger.warning(f"⚠️ Home batch calculation completed but storage failed - data cached")
            logger.info(f"📊 Batch {batch_id} calculation took {job_duration.total_seconds():.2f}s")
            logger.info(f"🎯 Calculated tickers: {[t['ticker'] for t in top_tickers]}")

            return {
                "status": "calculated_and_cached",
                "batch_id": batch_id,
                "top_tickers_count": len(top_tickers),
                "total_mentions": total_mentions_count,
                "duration_seconds": job_duration.total_seconds(),
            }

    except Exception as e:
        job_duration = datetime.now() - job_start_time
        logger.error(f"❌ Home batch data job failed after {job_duration.total_seconds():.2f}s: {e}")
        raise