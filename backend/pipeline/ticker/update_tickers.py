#!/usr/bin/env python3
"""
Cron job script to update ticker data from SEC.
Run this script periodically to keep ticker data fresh.

Usage: python update_tickers.py
Crontab example: 0 2 * * 0 cd /path/to/backend && python update_tickers.py >> ticker_updates.log 2>&1
"""

import sys
import os
from datetime import datetime

# Add current directory to path so we can import ticker modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ticker_manager import TickerManager

def main():
    """Update ticker data and log results."""
    print(f"🕐 Starting ticker update at {datetime.now()}")
    
    try:
        # Create ticker manager (will use existing cache if present)
        manager = TickerManager()
        
        # Force update regardless of cache age
        print("🔄 Forcing ticker data update from SEC...")
        success = manager.force_update()
        
        if success:
            print(f"✅ Successfully updated {manager.get_ticker_count()} tickers")
            print(f"✅ Reverse company mappings: {len(manager.reverse_company_map)}")
        else:
            print("❌ Failed to update ticker data")
            return 1
            
    except Exception as e:
        print(f"❌ Error during ticker update: {e}")
        return 1
    
    print(f"🏁 Ticker update completed at {datetime.now()}")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)