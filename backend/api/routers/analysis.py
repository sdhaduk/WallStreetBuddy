"""
Stock Analysis endpoints for AI-generated reports
"""
from fastapi import APIRouter, HTTPException, Request
from elasticsearch import Elasticsearch
import logging
from datetime import datetime

from ..config import settings
from ..services.stock_researcher_agent import stock_analysis_service

router = APIRouter()
logger = logging.getLogger(__name__)


def get_elasticsearch_client():
    return Elasticsearch([settings.elasticsearch_url])


@router.post("/analysis/generate-batch")
async def generate_batch_analysis(request: Request):
    """
    Internal endpoint to generate analysis reports for top 10 tickers from last 3 days
    This endpoint is intended to be called by the scheduler
    """
    api_key = request.headers.get("X-Internal-API-Key")
    if not api_key or api_key != settings.internal_api_key:
        raise HTTPException(status_code=403, detail="Access denied: Invalid or missing internal API key")

    try:
        es = get_elasticsearch_client()

        # Get latest batch data for perfect consistency with home page
        batch_resp = es.search(
            index="home-batch-*",
            size=1,
            sort=[{"@timestamp": {"order": "desc"}}],
            query={"match_all": {}}
        )

        batch_hits = batch_resp.body.get("hits", {}).get("hits", [])

        if not batch_hits:
            logger.warning("No batch data found for analysis")
            return {
                "status": 200,
                "message": "No batch data available for analysis. Home batch job may not have run yet."
            }

        batch_data = batch_hits[0]["_source"]
        batch_id = batch_data.get("batch_id", "unknown")
        symbols = [ticker["ticker"] for ticker in batch_data.get("top_tickers", [])]

        if not symbols:
            logger.warning(f"No tickers in batch data {batch_id}")
            return {
                "status": 200,
                "message": f"No tickers found in batch {batch_id}"
            }
        logger.info(f"Generating batch analysis for {batch_id} - {len(symbols)} tickers: {symbols}")

        reports = await stock_analysis_service.generate_batch_reports(symbols)

        # Calculate index name once for consistent batch storage
        generation_time = datetime.now()
        index_name = f"stock-analysis-{generation_time.strftime('%Y.%m.%d')}"
        generation_time_iso = generation_time.isoformat()

        logger.info(f"Storing batch reports in index: {index_name}")

        # Track failures with content preservation for scheduler retry
        successful_reports = 0
        failed_symbols = []
        failed_report_data = {}

        for symbol, report_content in reports.items():
            if report_content is not None:
                storage_success = await store_analysis_report(es, symbol, report_content, index_name, generation_time_iso)

                if storage_success:
                    successful_reports += 1
                else:
                    failed_symbols.append(symbol)
                    failed_report_data[symbol] = report_content
                    logger.warning(f"⚠️ Cached report for {symbol} due to storage failure")
            else:
                # Report generation failed - no content to retry
                failed_symbols.append(symbol)
                logger.error(f"❌ Report generation failed for {symbol}")

        total_failed = len(failed_symbols)
        logger.info(f"Batch analysis completed: {successful_reports} successful, {total_failed} failed")

        if failed_report_data:
            logger.info(f"💾 Preserved {len(failed_report_data)} reports for scheduler retry")

        return {
            "status": 201,
            "total_tickers": len(symbols),
            "successful_reports": successful_reports,
            "failed_reports": failed_symbols,
            "failed_report_data": failed_report_data,
            "index_name": index_name,
            "generation_time": generation_time_iso,
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
            return {
                "status": 200,
                "ticker": ticker.upper(),
                "generation_time": None,
                "report_content": "Analysis report will be available after it completes generating... come back in 5 minutes.",
                "report_status": "pending"
            }

        report = hits[0]["_source"]
        return {
            "status": 200,
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
            "status": 200,
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

        report_content = await stock_analysis_service.generate_report(ticker)

        if not report_content:
            raise HTTPException(status_code=500, detail=f"Failed to generate report for {ticker}")

        es = get_elasticsearch_client()

        await store_analysis_report(es, ticker, report_content)

        logger.info(f"Successfully generated and stored report for {ticker}")

        return {
            "status": 201,
            "ticker": ticker,
            "generation_time": datetime.now().isoformat(),
            "message": f"Analysis report generated successfully for {ticker}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate report for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


async def store_analysis_report(es: Elasticsearch, ticker: str, report_content: str, index_name: str, generation_time: str) -> bool:
    """
    Store analysis report in Elasticsearch

    Args:
        es: Elasticsearch client
        ticker: Stock ticker symbol
        report_content: Generated report content
        index_name: Elasticsearch index name for consistent batch storage
        generation_time: ISO timestamp for when the report was generated

    Returns:
        bool: True if storage successful, False if failed
    """
    try:
        doc = {
            "@timestamp": generation_time,
            "ticker": ticker.upper(),
            "generation_time": generation_time,
            "report_content": report_content,
            "status": "completed",
            "model_used": "gpt-5",
        }

        result = es.index(
            index=index_name,
            document=doc
        )

        logger.info(f"✅ Stored analysis report for {ticker} in index {index_name}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to store analysis report for {ticker} in {index_name}: {e}")
        return False