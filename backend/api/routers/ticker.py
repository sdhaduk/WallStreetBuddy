"""
Ticker check endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from elasticsearch import Elasticsearch
import logging
import json
import base64
from typing import Optional
from datetime import datetime

from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def format_timestamp(timestamp_str: str) -> str:
    """
    Convert timestamp to user-friendly format
    Handles both processed_timestamp format ("2025-09-21 19:07:33.274") and ISO format
    """
    try:
        # Handle processed_timestamp format: "YYYY-MM-DD HH:MM:SS.mmm"
        if ' ' in timestamp_str and not 'T' in timestamp_str:
            # Remove microseconds if present and parse
            timestamp_clean = timestamp_str.split('.')[0]  # Remove .274 part
            dt = datetime.strptime(timestamp_clean, "%Y-%m-%d %H:%M:%S")
        else:
            # Handle ISO format timestamps
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

        # Format as: "Jan 15, 2024 at 2:30 PM"
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except (ValueError, AttributeError) as e:
        # Fallback to original timestamp if parsing fails
        print(f"Timestamp parsing failed for '{timestamp_str}': {e}")
        return timestamp_str


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


@router.get("/comments")
async def get_comments(
    timeframe: str,
    tickers: Optional[str] = None,
    subreddit: str = "all",
    cursor: Optional[str] = None,
    size: int = Query(default=50, le=50, ge=1)
):
    """
    Get comments filtered by timeframe, tickers, and subreddit with cursor-based pagination

    Args:
        timeframe: String like "3d", "90m", "2h" (frontend validated)
        tickers: Comma-separated ticker list (e.g., "AAPL,TSLA") or None for all
        subreddit: "all", "wallstreetbets", "stocks", or "ValueInvesting"
        cursor: Base64 encoded timestamp for pagination (None for first page)
        size: Number of results to return (1-50, default 50)
    """
    try:
        # Build base time query
        must_queries = [
            {
                "range": {
                    "@timestamp": {
                        "gte": f"now-{timeframe}"
                    }
                }
            }
        ]

        # Add subreddit filter if not "all"
        if subreddit != "all":
            must_queries.append({
                "term": {"subreddit": subreddit}
            })

        # Add ticker filter if provided
        if tickers and tickers.strip():
            ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
            if ticker_list:
                must_queries.append({
                    "terms": {"tickers": ticker_list}
                })

        # Build the main query
        query = {
            "bool": {
                "must": must_queries
            }
        }

        # Build the search body
        search_body = {
            "size": size,
            "sort": [
                {"@timestamp": {"order": "desc"}},
                {"id": {"order": "desc"}}  # Tie-breaker for identical timestamps
            ],
            "_source": ["id", "body", "subreddit", "timestamp", "tickers", "processed_at"],
            "query": query
        }

        # Add search_after for cursor-based pagination
        if cursor:
            try:
                decoded_cursor = base64.b64decode(cursor).decode('utf-8')
                # For cursor-based pagination, we need both timestamp and id
                # Cursor format: "timestamp,id" base64 encoded
                if ',' in decoded_cursor:
                    timestamp_str, doc_id = decoded_cursor.split(',', 1)
                    search_body["search_after"] = [timestamp_str, doc_id]
                else:
                    # Fallback for simple timestamp cursor
                    search_body["search_after"] = [decoded_cursor]
            except Exception as cursor_error:
                logger.warning(f"Invalid cursor format: {cursor_error}")
                # Continue without cursor (start from beginning)

        # Execute the search
        es = Elasticsearch([settings.elasticsearch_url])
        resp = es.search(
            index="ticker-mentions-*",
            body=search_body
        )

        data = resp.body
        hits = data.get("hits", {}).get("hits", [])

        # Format data for frontend
        comments = []
        last_sort_values = None

        for hit in hits:
            source = hit["_source"]

            comments.append({
                "id": source.get("id", hit["_id"]),
                "body": source.get("body", ""),
                "subreddit": source.get("subreddit", ""),
                "timestamp": format_timestamp(source.get("processed_at", "")),
                "tickers": source.get("tickers", [])
            })
            # Keep track of the last document's sort values for next cursor
            last_sort_values = hit.get("sort")

        # Generate next cursor if we have results and potentially more data
        next_cursor = None
        has_next = len(comments) == size  # If we got full page, likely more data

        if has_next and last_sort_values and len(last_sort_values) >= 2:
            # Create cursor from timestamp and id
            cursor_data = f"{last_sort_values[0]},{last_sort_values[1]}"
            next_cursor = base64.b64encode(cursor_data.encode('utf-8')).decode('utf-8')

        # Build response
        response = {
            "status": 200,
            "data": comments,
            "pagination": {
                "size": size,
                "has_next": has_next,
                "total_returned": len(comments)
            },
            "filters": {
                "timeframe": timeframe,
                "subreddit": subreddit
            }
        }

        # Add next_cursor and tickers to response if applicable
        if next_cursor:
            response["pagination"]["next_cursor"] = next_cursor

        if tickers and tickers.strip():
            response["filters"]["tickers"] = [t.strip().upper() for t in tickers.split(",") if t.strip()]

        return response

    except Exception as e:
        logger.error(f"Comments query failed: {e}")
        raise HTTPException(status_code=500, detail="Comments query failed")

