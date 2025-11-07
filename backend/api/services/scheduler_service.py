"""
APScheduler service for WallStreetBuddy background tasks
"""
import logging
import inspect
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
        from datetime import datetime, timedelta
        from ..scheduler.jobs import stock_analysis_job, home_batch_data_job

        # Calculate start times for deployment and production jobs
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.date import DateTrigger
        now = datetime.now()

        # Deployment jobs: immediate data generation after startup (run once only)
        home_deployment_start = now + timedelta(minutes=10000)
        analysis_deployment_start = now + timedelta(minutes=10000)  # 7 minutes from now (2 minutes after batch)

        # HOME BATCH JOBS
        # Deployment job - runs ONCE in 5 minutes for immediate data after deployment
        self.scheduler.add_job(
            home_batch_data_job,
            trigger=DateTrigger(run_date=home_deployment_start),
            id='home_batch_data_deployment',
            name='Home Batch Data Deployment (One-time)',
            max_instances=1,
            replace_existing=True
        )

        # Production job - every 3 days at midnight starting from deployment+3 days
        home_production_start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=3)
        self.scheduler.add_job(
            home_batch_data_job,
            trigger=IntervalTrigger(days=3, start_date=home_production_start),
            id='home_batch_data_production',
            name='Home Batch Data Production (Every 3 Days)',
            max_instances=1,
            replace_existing=True
        )

        # STOCK ANALYSIS JOBS
        # Deployment job - runs ONCE in 7 minutes for immediate analysis after deployment
        self.scheduler.add_job(
            stock_analysis_job,
            trigger=DateTrigger(run_date=analysis_deployment_start),
            id='stock_analysis_deployment',
            name='Stock Analysis Deployment (One-time)',
            max_instances=1,
            replace_existing=True
        )

        # Production job - every 3 days, 15 minutes after home batch job
        analysis_production_start = home_production_start + timedelta(minutes=15)
        self.scheduler.add_job(
            stock_analysis_job,
            trigger=IntervalTrigger(days=3, start_date=analysis_production_start),
            id='stock_analysis_production',
            name='Stock Analysis Production (Every 3 Days)',
            max_instances=1,
            replace_existing=True
        )

        logger.info("📅 Registered scheduled jobs:")
        logger.info(f"  - Home Batch Deployment: Run once at {home_deployment_start.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  - Home Batch Production: Every 3 days starting {home_production_start.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  - Stock Analysis Deployment: Run once at {analysis_deployment_start.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  - Stock Analysis Production: Every 3 days starting {analysis_production_start.strftime('%Y-%m-%d %H:%M:%S')}")

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

            # Execute job immediately (handle both sync and async functions)
            if inspect.iscoroutinefunction(job.func):
                await job.func()
            else:
                job.func()
            logger.info(f"✅ Manually triggered job '{job_id}'")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to trigger job '{job_id}': {e}")
            return False


# Global scheduler instance
scheduler_service = SchedulerService()