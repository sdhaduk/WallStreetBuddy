"""
Scheduled job definitions for WallStreetBuddy
"""
import logging
import httpx
from datetime import datetime

from ..config import settings

logger = logging.getLogger(__name__)


async def stock_analysis_job():
    """
    Scheduled job to generate analysis reports for top 10 tickers from last 3 days
    Runs every 3 days at 12:05 AM (5 minutes after data becomes available)

    Makes HTTP request to existing /api/analysis/generate-batch endpoint
    """
    job_start_time = datetime.now()
    logger.info(f"🚀 Starting scheduled stock analysis job at {job_start_time}")

    try:
        # Make HTTP POST request to the existing endpoint
        base_url = f"http://{settings.fastapi_host}:{settings.fastapi_port}"
        endpoint_url = f"{base_url}{settings.api_prefix}/analysis/generate-batch"

        timeout = httpx.Timeout(300.0)  # 5 minute timeout for AI generation

        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"📡 Making request to {endpoint_url}")

            response = await client.post(endpoint_url)
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