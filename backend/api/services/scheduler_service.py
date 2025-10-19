"""
APScheduler service for WallStreetBuddy background tasks
"""
import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

logger = logging.getLogger(__name__)


class SchedulerService:
    """AsyncIO-compatible scheduler service for background tasks"""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._is_running = False

    async def start(self):
        """Start the scheduler service"""
        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        try:
            self.scheduler = AsyncIOScheduler()

            # Add event listeners for job monitoring
            self.scheduler.add_listener(
                self._job_executed_listener,
                EVENT_JOB_EXECUTED
            )
            self.scheduler.add_listener(
                self._job_error_listener,
                EVENT_JOB_ERROR
            )

            # Add scheduled jobs
            await self._register_jobs()

            # Start the scheduler
            self.scheduler.start()
            self._is_running = True

            logger.info("✅ Scheduler service started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start scheduler service: {e}")
            raise

    async def stop(self):
        """Stop the scheduler service"""
        if not self._is_running or not self.scheduler:
            return

        try:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("✅ Scheduler service stopped successfully")

        except Exception as e:
            logger.error(f"❌ Failed to stop scheduler service: {e}")
            raise

    async def _register_jobs(self):
        """Register all scheduled jobs"""
        from ..scheduler.jobs import stock_analysis_job

        # Stock Analysis Job - Every 3 days at 12:05 AM 
        self.scheduler.add_job(
            stock_analysis_job,
            trigger=CronTrigger(
                hour=0,
                minute=5,
                day='*/3'
            ),
            id='stock_analysis_batch',
            name='Stock Analysis Batch Generation',
            max_instances=1,
            replace_existing=True
        )

        logger.info("📅 Registered scheduled jobs:")
        logger.info("  - Stock Analysis: Every 3 days at 12:05 AM")

    def _job_executed_listener(self, event):
        """Handle successful job execution"""
        logger.info(
            f"✅ Job '{event.job_id}' executed successfully "
            f"in {event.scheduled_run_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def _job_error_listener(self, event):
        """Handle job execution errors"""
        logger.error(
            f"❌ Job '{event.job_id}' failed: {event.exception}"
        )

    def get_status(self) -> dict:
        """Get scheduler status and job information"""
        if not self.scheduler:
            return {"status": "not_initialized", "jobs": []}

        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return {
            "status": "running" if self._is_running else "stopped",
            "jobs": jobs_info,
            "current_time": datetime.now().isoformat()
        }

    async def trigger_job(self, job_id: str) -> bool:
        """Manually trigger a specific job (for testing)"""
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False

        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                logger.error(f"Job '{job_id}' not found")
                return False

            # Execute job immediately
            job.func()
            logger.info(f"✅ Manually triggered job '{job_id}'")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to trigger job '{job_id}': {e}")
            return False


# Global scheduler instance
scheduler_service = SchedulerService()