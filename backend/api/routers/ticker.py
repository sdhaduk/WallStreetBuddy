"""
Ticker check endpoints
"""
from fastapi import APIRouter, HTTPException
from elasticsearch import Elasticsearch
import logging
import json

from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/top-10-filtered")
async def top_10_filtered(timeframe: str = "3d", subreddit: str = "all"):
    """
    Get top 10 tickers filtered by timeframe and subreddit

    Args:
        timeframe: String like "3d", "90m", "2h" (frontend validated)
        subreddit: "all", "wallstreetbets", "stocks", or "ValueInvesting"
    """
    try:
        # Build base time query
        query = {
            "range": {
                "@timestamp": {
                    "gte": f"now-{timeframe}"
                }
            }
        }

        # Add subreddit filter if not "all"
        if subreddit != "all":
            query = {
                "bool": {
                    "must": [
                        query,
                        {"term": {"subreddit": subreddit}}
                    ]
                }
            }

        es = Elasticsearch([settings.elasticsearch_url])
        resp = es.search(
            index="ticker-mentions-*",
            size=0,
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

        # Get total mentions count from the query hits
        total_mentions = data.get("hits", {}).get("total", {})
        if isinstance(total_mentions, dict):
            total_mentions_count = total_mentions.get("value", 0)
        else:
            total_mentions_count = total_mentions or 0

        # Format data for frontend
        result = []
        for bucket in buckets:
            result.append({
                "ticker": bucket["key"],
                "mentions": bucket["doc_count"]
            })

        return {
            "status": 200,
            "data": result,
            "total_mentions": total_mentions_count
        }

    except Exception as e:
        logger.error(f"Filtered query failed: {e}")
        raise HTTPException(status_code=500, detail="Filtered query failed")

