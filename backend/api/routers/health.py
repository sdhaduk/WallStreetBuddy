"""
Health check endpoints
"""
from fastapi import APIRouter, HTTPException
from elasticsearch import Elasticsearch
import logging

from ..config import settings
from ..services.scheduler_service import scheduler_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        es = Elasticsearch([settings.elasticsearch_url])
        health = es.cluster.health()
        
        return {
            "status": 200,
            "elasticsearch": {
                "status": health["status"],
                "cluster_name": health["cluster_name"],
                "number_of_nodes": health["number_of_nodes"]
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/scheduler/status")
async def scheduler_status():
    """Get scheduler status and job information"""
    try:
        status = scheduler_service.get_status()
        return {
            "status": 200,
            "scheduler": status
        }
    except Exception as e:
        logger.error(f"Scheduler status check failed: {e}")
        raise HTTPException(status_code=503, detail="Scheduler status unavailable")


@router.post("/scheduler/trigger/{job_id}")
async def trigger_job(job_id: str):
    """Manually trigger a scheduled job (for testing)"""
    try:
        success = await scheduler_service.trigger_job(job_id)
        if success:
            return {
                "status": 200,
                "message": f"Job '{job_id}' triggered successfully",
                "job_id": job_id
            }
        else:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger job '{job_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger job: {str(e)}")