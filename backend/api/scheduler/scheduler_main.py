#!/usr/bin/env python3
"""
Standalone scheduler service for WallStreetBuddy
This script runs ONLY the background scheduler, not the FastAPI server
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager

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


async def main():
    """Main scheduler service entry point"""
    global scheduler_service

    logger.info("🕐 Starting WallStreetBuddy Scheduler Service")
    logger.info(f"📊 Environment: {settings.debug}")
    logger.info(f"📡 Elasticsearch: {settings.elasticsearch_url}")

    try:
        # Initialize and start scheduler service
        scheduler_service = SchedulerService()
        await scheduler_service.start()

        logger.info("✅ Scheduler service is running...")
        logger.info("Press Ctrl+C to gracefully shutdown")

        # Keep the scheduler running until interrupted
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Scheduler service error: {e}")
        raise
    finally:
        # Graceful shutdown
        if scheduler_service:
            logger.info("🛑 Shutting down scheduler service...")
            await scheduler_service.stop()
            logger.info("✅ Scheduler service stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"🛑 Received signal {signum}")
    # This will trigger KeyboardInterrupt in the main loop
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Run the scheduler service
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("✅ Scheduler service stopped gracefully")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)