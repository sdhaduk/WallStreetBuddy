"""
Health check endpoints
"""
from fastapi import APIRouter, HTTPException
from elasticsearch import Elasticsearch
import logging

from ..config import settings

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