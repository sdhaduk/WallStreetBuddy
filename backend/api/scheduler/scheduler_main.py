#!/usr/bin/env python3
"""
Standalone scheduler service for WallStreetBuddy
This script runs ONLY the background scheduler, not the FastAPI server
"""

import asyncio
import logging
import signal
import sys
import time
from contextlib import asynccontextmanager
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError

from ..services.scheduler_service import SchedulerService
from ..config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global scheduler instance for graceful shutdown
scheduler_service = None

# Retry configuration
MAX_RETRY_ATTEMPTS = 5
INITIAL_BACKOFF_DELAY = 5  # seconds
MAX_BACKOFF_DELAY = 300    # 5 minutes
BACKOFF_MULTIPLIER = 2


async def wait_for_elasticsearch_connection():
    """Wait for Elasticsearch to be available with exponential backoff"""
    attempt = 1
    delay = INITIAL_BACKOFF_DELAY

    while attempt <= MAX_RETRY_ATTEMPTS:
        try:
            logger.info(f"🔍 Attempting Elasticsearch connection (attempt {attempt}/{MAX_RETRY_ATTEMPTS})")
            es = Elasticsearch([settings.elasticsearch_url])

            health = es.cluster.health()
            logger.info(f"✅ Elasticsearch connected successfully - Status: {health.get('status', 'unknown')}")
            return True

        except (ESConnectionError, Exception) as e:
            logger.warning(f"⚠️ Elasticsearch connection failed (attempt {attempt}/{MAX_RETRY_ATTEMPTS}): {e}")

            if attempt == MAX_RETRY_ATTEMPTS:
                logger.error(f"❌ Failed to connect to Elasticsearch after {MAX_RETRY_ATTEMPTS} attempts")
                return False

            logger.info(f"⏳ Retrying in {delay} seconds...")
            await asyncio.sleep(delay)

            delay = min(delay * BACKOFF_MULTIPLIER, MAX_BACKOFF_DELAY)
            attempt += 1

    return False


async def start_scheduler_with_retry():
    """Start the scheduler service with retry logic and error recovery"""
    global scheduler_service

    while True:  # Infinite retry loop for critical service
        try:
            if not await wait_for_elasticsearch_connection():
                logger.error("❌ Cannot start scheduler without Elasticsearch connection")
                logger.info(f"⏳ Retrying complete startup in {INITIAL_BACKOFF_DELAY} seconds...")
                await asyncio.sleep(INITIAL_BACKOFF_DELAY)
                continue

            logger.info("🚀 Initializing scheduler service...")
            scheduler_service = SchedulerService()
            await scheduler_service.start()

            logger.info("✅ Scheduler service started successfully")
            return scheduler_service

        except Exception as e:
            logger.error(f"❌ Failed to start scheduler service: {e}")
            logger.info(f"⏳ Retrying scheduler startup in {INITIAL_BACKOFF_DELAY} seconds...")

            if scheduler_service:
                try:
                    await scheduler_service.stop()
                except Exception:
                    pass
                scheduler_service = None

            await asyncio.sleep(INITIAL_BACKOFF_DELAY)


async def monitor_scheduler_health():
    """Monitor scheduler health and restart if needed"""
    global scheduler_service

    while True:
        try:
            await asyncio.sleep(30)

            if not scheduler_service or not scheduler_service._is_running:
                logger.warning("⚠️ Scheduler service appears to be stopped, attempting restart...")
                scheduler_service = await start_scheduler_with_retry()

        except Exception as e:
            logger.error(f"❌ Health monitor error: {e}")
            await asyncio.sleep(INITIAL_BACKOFF_DELAY)


async def main():
    """Main scheduler service entry point with robust error handling"""
    global scheduler_service

    logger.info("🕐 Starting WallStreetBuddy Scheduler Service")
    logger.info(f"📊 Environment: {settings.debug}")
    logger.info(f"📡 Elasticsearch: {settings.elasticsearch_url}")
    logger.info(f"🔄 Retry configuration: {MAX_RETRY_ATTEMPTS} attempts, {INITIAL_BACKOFF_DELAY}s initial delay")

    try:
        scheduler_service = await start_scheduler_with_retry()

        logger.info("✅ Scheduler service is running...")
        logger.info("🩺 Starting health monitor...")

        health_monitor_task = asyncio.create_task(monitor_scheduler_health())

        logger.info("📡 Scheduler ready and running")

        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"❌ Critical scheduler error: {e}")
        logger.error("💥 Scheduler service will restart...")
        raise
    finally:
        if scheduler_service:
            logger.info("🛑 Shutting down scheduler service...")
            try:
                await scheduler_service.stop()
                logger.info("✅ Scheduler service stopped successfully")
            except Exception as e:
                logger.error(f"❌ Error during scheduler shutdown: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"🛑 Received signal {signum}")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)