"""
APScheduler service for WallStreetBuddy background tasks
"""
import logging
import inspect
import os
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

logger = logging.getLogger(__name__)


class SchedulerService:
    """AsyncIO-compatible scheduler service for background tasks"""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._is_running = False
        self.scheduler_data_dir = "/var/scheduler"
        self.deployment_marker_file = os.path.join(self.scheduler_data_dir, "deployment_complete")

    async def start(self):
        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        try:
            os.makedirs(self.scheduler_data_dir, exist_ok=True)

            jobstores = {
                'default': SQLAlchemyJobStore(url=f'sqlite:///{self.scheduler_data_dir}/jobs.db')
            }

            job_defaults = {
                'coalesce': False,      # Execute missed jobs (maintains data completeness)
                'max_instances': 1,     # Prevent multiple instances
                'misfire_grace_time': 300  # 5 minutes grace period for brief restarts
            }

            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                job_defaults=job_defaults
            )

            self.scheduler.add_listener(
                self._job_executed_listener,
                EVENT_JOB_EXECUTED
            )
            self.scheduler.add_listener(
                self._job_error_listener,
                EVENT_JOB_ERROR
            )

            await self._register_jobs()

            self.scheduler.start()
            self._is_running = True

            logger.info("✅ Scheduler service started successfully")

            # Log restored jobs if this was a restart after deployment
            if hasattr(self, '_log_restored_jobs_after_start'):
                self._log_restored_jobs()
                delattr(self, '_log_restored_jobs_after_start')

        except Exception as e:
            logger.error(f"❌ Failed to start scheduler service: {e}")
            raise

    async def stop(self):
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
        from ..scheduler.jobs import stock_analysis_job, home_batch_data_job, process_cached_results
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.date import DateTrigger
        now = datetime.now()

        # Check if this is first deployment or restart
        if not os.path.exists(self.deployment_marker_file):
            logger.info("🆕 First deployment detected - scheduling all jobs")

            # Deployment jobs (run once)
            home_deployment_start = now + timedelta(minutes=5)
            analysis_deployment_start = now + timedelta(minutes=7)

            self.scheduler.add_job(
                home_batch_data_job,
                trigger=DateTrigger(run_date=home_deployment_start),
                id='home_batch_data_deployment',
                name='Home Batch Data Deployment (One-time)',
                max_instances=1,
                replace_existing=True
            )

            self.scheduler.add_job(
                stock_analysis_job,
                trigger=DateTrigger(run_date=analysis_deployment_start),
                id='stock_analysis_deployment',
                name='Stock Analysis Deployment (One-time)',
                max_instances=1,
                replace_existing=True
            )

            # Production jobs (every 3 days starting in 3 days)
            production_start = (now + timedelta(days=3)).replace(hour=0, minute=0, second=0, microsecond=0)
            analysis_production_start = production_start + timedelta(minutes=15)

            self.scheduler.add_job(
                home_batch_data_job,
                trigger=IntervalTrigger(days=3, start_date=production_start),
                id='home_batch_data_production',
                name='Home Batch Data Production (Every 3 Days)',
                max_instances=1,
                replace_existing=True
            )

            self.scheduler.add_job(
                stock_analysis_job,
                trigger=IntervalTrigger(days=3, start_date=analysis_production_start),
                id='stock_analysis_production',
                name='Stock Analysis Production (Every 3 Days)',
                max_instances=1,
                replace_existing=True
            )

            # Create deployment marker to prevent re-scheduling on restart
            os.makedirs(os.path.dirname(self.deployment_marker_file), exist_ok=True)
            with open(self.deployment_marker_file, 'w') as f:
                f.write(now.isoformat())

            logger.info("📅 All jobs scheduled successfully:")
            logger.info(f"  - Home Batch Deployment: {home_deployment_start.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"  - Stock Analysis Deployment: {analysis_deployment_start.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"  - Home Batch Production: Every 3 days starting {production_start.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"  - Stock Analysis Production: Every 3 days starting {analysis_production_start.strftime('%Y-%m-%d %H:%M:%S')}")

        else:
            logger.info("✅ Deployment marker exists - SQLite JobStore will restore all jobs automatically")
            self._log_restored_jobs_after_start = True

        # Always schedule background cache processor
        cache_processor_start = now + timedelta(minutes=5)
        self.scheduler.add_job(
            process_cached_results,
            trigger=IntervalTrigger(minutes=10, start_date=cache_processor_start),
            id='cache_processor',
            name='Background Cache Processor',
            max_instances=1,
            replace_existing=True
        )

    def _job_executed_listener(self, event):
        logger.info(
            f"✅ Job '{event.job_id}' executed successfully "
            f"in {event.scheduled_run_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def _job_error_listener(self, event):
        logger.error(
            f"❌ Job '{event.job_id}' failed: {event.exception}"
        )

    def get_status(self) -> dict:
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
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return False

        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                logger.error(f"Job '{job_id}' not found")
                return False

            if inspect.iscoroutinefunction(job.func):
                await job.func()
            else:
                job.func()
            logger.info(f"✅ Manually triggered job '{job_id}'")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to trigger job '{job_id}': {e}")
            return False

    def _log_restored_jobs(self):
        """Log jobs that were restored from SQLite after restart"""
        try:
            logger.info("📋 Jobs restored from SQLite JobStore:")

            all_jobs = self.scheduler.get_jobs()
            for job in all_jobs:
                if job.next_run_time:
                    next_run_local = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
                    logger.info(f"  - {job.name} (ID: {job.id}): Next run = {next_run_local}")
                else:
                    logger.info(f"  - {job.name} (ID: {job.id}): Completed (no next run)")

            if not all_jobs:
                logger.warning("  - No jobs found in SQLite JobStore")

        except Exception as e:
            logger.error(f"❌ Error logging restored jobs: {e}")


# Global scheduler instance
scheduler_service = SchedulerService()