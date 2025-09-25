import asyncio
from datetime import datetime
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from .yahoo_finance import YahooFinance
import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Load system prompt from environment variable
system_prompt = os.getenv("STOCK_ANALYSIS_SYSTEM_PROMPT", "You are a financial analyst. Generate comprehensive stock research reports in markdown format.")

openai_api_key = os.getenv("OPENAI_API_KEY")
    
model_settings = OpenAIResponsesModelSettings(
    temperature=0.2,
    max_tokens=8000
)

model = OpenAIResponsesModel('gpt-5-2025-08-07', provider=OpenAIProvider(api_key=openai_api_key))

agent = Agent(
    name='Stock Researcher Agent',
    model=model,
    model_settings=model_settings,
    system_prompt=system_prompt,
    tools=[
        YahooFinance.get_current_price,
        YahooFinance.get_company_info,
        YahooFinance.get_historical_stock_prices,
        YahooFinance.get_stock_fundamentals,
        YahooFinance.get_income_statements,
        YahooFinance.get_key_financial_ratios,
        YahooFinance.get_analyst_recommendations,
        YahooFinance.get_company_news,
        YahooFinance.get_technical_indicators,
    ]
)

@agent.system_prompt
def today_date() -> str:
    return f"Today is {datetime.today().strftime('%Y-%m-%d')}"


class StockAnalysisService:
    """Service class for generating stock analysis reports using async pydantic-ai"""

    def __init__(self, max_concurrent_requests: int = 3):
        self.agent = agent
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def generate_report(self, symbol: str) -> str:
        """Generate analysis report for a stock symbol using async agent.run()"""
        async with self.semaphore:
            try:
                logger.info(f"Generating report for {symbol}")

                # Special handling for ETFs
                symbol_upper = symbol.upper()
                if symbol_upper == "SPY":
                    logger.info(f"Special handling for SPY - returning custom message")
                    return "Its SPY buddy."
                elif symbol_upper == "QQQM":
                    logger.info(f"Special handling for QQQM - returning custom message")
                    return "Its QQQM buddy."

                # Generate normal analysis report
                prompt = f"Generate an executive report for {symbol}"
                result = await self.agent.run(prompt)
                logger.info(f"Successfully generated report for {symbol}")
                return result.output
            except Exception as e:
                logger.error(f"Report generation failed for {symbol}: {e}")
                raise

    async def generate_batch_reports(self, symbols: List[str]) -> Dict[str, Optional[str]]:
        """Generate reports for multiple symbols with concurrency control"""
        logger.info(f"Starting batch generation for {len(symbols)} symbols: {symbols}")

        # Create tasks for concurrent execution
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(
                self._safe_generate_report(symbol),
                name=f"report_generation_{symbol}"
            )
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build result dictionary
        reports = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to generate report for {symbol}: {result}")
                reports[symbol] = None
            else:
                reports[symbol] = result

        successful_count = sum(1 for r in reports.values() if r is not None)
        logger.info(f"Batch generation completed: {successful_count}/{len(symbols)} successful")

        return reports

    async def _safe_generate_report(self, symbol: str) -> Optional[str]:
        """Safely generate a report with individual error handling"""
        try:
            return await self.generate_report(symbol)
        except Exception as e:
            logger.error(f"Safe report generation failed for {symbol}: {e}")
            return None


# Global service instance
stock_analysis_service = StockAnalysisService()