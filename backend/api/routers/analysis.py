"""
Stock Analysis endpoints for AI-generated reports
"""
from fastapi import APIRouter, HTTPException
from elasticsearch import Elasticsearch
import logging
from datetime import datetime

from ..config import settings
from ..services.stock_researcher_agent import stock_analysis_service

router = APIRouter()
logger = logging.getLogger(__name__)


def get_elasticsearch_client():
    """Get Elasticsearch client"""
    return Elasticsearch([settings.elasticsearch_url])


@router.post("/analysis/generate-batch")
async def generate_batch_analysis():
    """
    Internal endpoint to generate analysis reports for top 10 tickers from last 3 days
    This endpoint is intended to be called by the scheduler
    """
    try:
        # Get top 10 tickers from the existing ticker endpoint logic
        es = get_elasticsearch_client()

        # Query for top 10 tickers in the previous 3-day batch (day -6 to day -3)
        # This matches the Home page logic: shows completed 3-day batches, not rolling window
        query = {
            "range": {
                "@timestamp": {
                    "gte": "now-6d/d",  # Start 6 days ago at start of day
                    "lt": "now-3d/d"    # End 3 days ago at start of day
                }
            }
        }

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

        if not buckets:
            logger.warning("No tickers found in last 3 days")
            return {"status": "no_data", "message": "No tickers found in last 3 days"}

        # Extract ticker symbols
        symbols = [bucket["key"] for bucket in buckets]
        logger.info(f"Generating batch analysis for top {len(symbols)} tickers: {symbols}")

        # Generate reports using the async service
        reports = await stock_analysis_service.generate_batch_reports(symbols)

        # Store successful reports in Elasticsearch
        successful_reports = 0
        failed_reports = 0

        for symbol, report_content in reports.items():
            if report_content is not None:
                try:
                    await store_analysis_report(es, symbol, report_content)
                    successful_reports += 1
                except Exception as e:
                    logger.error(f"Failed to store report for {symbol}: {e}")
                    failed_reports += 1
            else:
                failed_reports += 1

        logger.info(f"Batch analysis completed: {successful_reports} successful, {failed_reports} failed")

        return {
            "status": "completed",
            "total_tickers": len(symbols),
            "successful_reports": successful_reports,
            "failed_reports": failed_reports,
            "generation_time": datetime.now().isoformat(),
            "tickers_processed": symbols
        }

    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.get("/analysis/report/{ticker}")
async def get_latest_report(ticker: str):
    """
    Get the latest analysis report for a specific ticker

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, TSLA)
    """
    try:
        es = get_elasticsearch_client()

        # Search for latest report for the ticker
        resp = es.search(
            index="stock-analysis-*",
            size=1,
            sort=[{"generation_time": {"order": "desc"}}],
            query={
                "term": {"ticker": ticker.upper()}
            }
        )

        hits = resp.body.get("hits", {}).get("hits", [])

        if not hits:
            raise HTTPException(status_code=404, detail=f"No analysis report found for {ticker}")

        report = hits[0]["_source"]
        return {
            "status": "found",
            "ticker": report.get("ticker"),
            "generation_time": report.get("generation_time"),
            "report_content": report.get("report_content"),
            "report_status": report.get("status", "completed")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve report for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report")


@router.get("/analysis/reports")
async def list_available_reports(days: int = 4):
    """
    Get list of all available analysis reports

    Args:
        days: Number of days to look back (default: 4, max retention)
    """
    try:
        es = get_elasticsearch_client()

        # Limit days to reasonable range
        days = min(max(days, 1), 7)

        resp = es.search(
            index="stock-analysis-*",
            size=100,
            sort=[{"generation_time": {"order": "desc"}}],
            query={
                "range": {
                    "generation_time": {
                        "gte": f"now-{days}d"
                    }
                }
            },
            _source=["ticker", "generation_time", "status"]
        )

        hits = resp.body.get("hits", {}).get("hits", [])

        reports = []
        for hit in hits:
            source = hit["_source"]
            reports.append({
                "ticker": source.get("ticker"),
                "generation_time": source.get("generation_time"),
                "status": source.get("status", "completed")
            })

        return {
            "status": "success",
            "total_reports": len(reports),
            "days_searched": days,
            "reports": reports
        }

    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to list reports")


@router.post("/analysis/generate/{ticker}")
async def generate_single_report(ticker: str):
    """
    Internal endpoint to generate analysis report for a specific ticker

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, TSLA)
    """
    try:
        ticker = ticker.upper()
        logger.info(f"Generating single report for {ticker}")

        # Generate report using the async service
        report_content = await stock_analysis_service.generate_report(ticker)

        if not report_content:
            raise HTTPException(status_code=500, detail=f"Failed to generate report for {ticker}")

        # Store report in Elasticsearch
        es = get_elasticsearch_client()

        await store_analysis_report(es, ticker, report_content)

        logger.info(f"Successfully generated and stored report for {ticker}")

        return {
            "status": "completed",
            "ticker": ticker,
            "generation_time": datetime.now().isoformat(),
            "message": f"Analysis report generated successfully for {ticker}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate report for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


async def store_analysis_report(es: Elasticsearch, ticker: str, report_content: str):
    """
    Store analysis report in Elasticsearch

    Args:
        es: Elasticsearch client
        ticker: Stock ticker symbol
        report_content: Generated report content
    """
    now = datetime.now()
    doc = {
        "@timestamp": now.isoformat(),
        "ticker": ticker.upper(),
        "generation_time": now.isoformat(),
        "report_content": report_content,
        "status": "completed",
        "model_used": "gpt-4o",  # Update based on your model
        "generation_duration_ms": 0  # Could be tracked if needed
    }

    # Use date-based index naming
    index_name = f"stock-analysis-{now.strftime('%Y.%m.%d')}"

    result = es.index(
        index=index_name,
        document=doc
    )

    logger.info(f"Stored analysis report for {ticker} in index {index_name}")
    return result