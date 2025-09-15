import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONSTANTS_DIR = BASE_DIR / "constants"
CONSTANTS_DIR.mkdir(exist_ok=True) 

class TickerManager:
    
    PREFERRED_TICKERS = {
        'microstrategy': 'MSTR',
        'berkshire hathaway': 'BRK.B',
    }
    
    def __init__(self, cache_days: int = 7):
        self.sec_url = "https://www.sec.gov/files/company_tickers.json"
        self.cache_file = CONSTANTS_DIR / "sec_tickers.json"
        self.cache_days = cache_days
        self.tickers: Set[str] = set()
        self.reverse_company_map: Dict[str, str] = {}
        self.last_updated: Optional[datetime] = None
        
        self._load_from_cache()
        
        if self._needs_update():
            self.update_tickers()
    
    def _needs_update(self) -> bool:
        """Check if ticker data needs to be updated."""
        if not self.last_updated:
            return True
        
        days_since_update = (datetime.now() - self.last_updated).days
        return days_since_update >= self.cache_days
    
    def _load_from_cache(self) -> bool:
        """Load ticker data from cache file."""
        try:
            if not os.path.exists(self.cache_file):
                return False
            
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                
            self.tickers = set(data.get('tickers', []))
            self.reverse_company_map = data.get('reverse_company_map', {})
            

            last_updated_str = data.get('last_updated')
            if last_updated_str:
                self.last_updated = datetime.fromisoformat(last_updated_str)
            
            print(f"✅ Loaded {len(self.tickers)} tickers from cache")
            return True
            
        except Exception as e:
            print(f"❌ Error loading ticker cache: {e}")
            return False
    
    def _save_to_cache(self) -> None:
        """Save ticker data to cache file using atomic operations."""
        try:
            data = {
                'tickers': list(self.tickers),
                'reverse_company_map': self.reverse_company_map,
                'last_updated': datetime.now().isoformat(),
                'total_count': len(self.tickers)
            }
            
            temp_file = self.cache_file.with_suffix(self.cache_file.suffix + ".tmp")
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            os.rename(str(temp_file), str(self.cache_file))
                
            print(f"✅ Saved {len(self.tickers)} tickers to cache")
            
        except Exception as e:
            print(f"❌ Error saving ticker cache: {e}")
            temp_file = self.cache_file.with_suffix(self.cache_file.suffix + ".tmp")
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def update_tickers(self) -> bool:
        """Fetch latest ticker data from SEC."""
        try:
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; TickerBot/1.0; +reddit-pipeline)',
                'Accept': 'application/json'
            }
            
            response = requests.get(self.sec_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            sec_data = response.json()

            new_tickers = set()
            new_reverse_company_map = {}
            manual_mapping = self._load_manual_mapping()
            
            for entry in sec_data.values():
                if isinstance(entry, dict) and 'ticker' in entry:
                    ticker = entry['ticker'].upper()
                    company_name = entry.get('title', '')
                    
                    new_tickers.add(ticker)

                    if company_name:
                        if company_name in manual_mapping:
                            normalized_name = manual_mapping[company_name]
                        else:
                            normalized_name = self._normalize_company_name(company_name)
                            print(f"🆕 New company {ticker}: '{company_name}' → '{normalized_name}'")
                        
                        if normalized_name:
                            if normalized_name in self.PREFERRED_TICKERS:
                                preferred_ticker = self.PREFERRED_TICKERS[normalized_name]
                                new_reverse_company_map[normalized_name] = preferred_ticker
                            else:
                                current_ticker = new_reverse_company_map.get(normalized_name)
                                if current_ticker is None or len(ticker) < len(current_ticker):
                                    new_reverse_company_map[normalized_name] = ticker
            
            self.tickers = new_tickers
            self.reverse_company_map = new_reverse_company_map
            self.last_updated = datetime.now()
            
            self._save_to_cache()
            
            print(f"✅ Updated {len(self.tickers)} tickers from SEC")
            return True
            
        except Exception as e:
            print(f"❌ Error fetching ticker data from SEC: {e}")
            return False
    
    def is_valid_ticker(self, ticker: str) -> bool:
        """Check if a ticker is valid according to SEC data."""
        if not ticker:
            return False
        return ticker.upper() in self.tickers
    
    
    def get_all_tickers(self) -> Set[str]:
        """Get all valid tickers."""
        return self.tickers.copy()
    
    def get_ticker_count(self) -> int:
        """Get total number of tickers."""
        return len(self.tickers)
    
    def force_update(self) -> bool:
        """Force update regardless of cache age."""
        return self.update_tickers()
    
    def _load_manual_mapping(self) -> Dict[str, str]:
        """Load static manual company name to normalized name mapping."""
        manual_mapping_file = CONSTANTS_DIR / "manual_ticker_mapping.json"
        try:
            if os.path.exists(manual_mapping_file):
                with open(manual_mapping_file, 'r') as f:
                    mapping = json.load(f)
                    print(f"✅ Loaded {len(mapping)} manual ticker mappings")
                    return mapping
            else:
                print("ℹ️ No manual mapping file found, will normalize all tickers")
            return {}
        except Exception as e:
            print(f"⚠️ Error loading manual mapping: {e}")
            return {}
    
    def _normalize_company_name(self, company_name: str) -> str:
        if not company_name:
            return ""
        
        normalized = company_name.lower().strip()

        suffixes_to_remove = [
            ' acquisition corp', ' income fund', ' income trust', ' limited/adr', 
            ' therapeutics inc', ' technologies inc', ' technologies, inc.', ' technologies, inc', ' pharmaceuticals inc',
            ' financial corp', ' financial inc', ' biosciences inc', ' technology inc', ' holdings inc', ' holdings ltd', ' holdings corp', ' holding ltd', ' holding corp', ' group inc', ' group ltd', ' bancorp inc', ' capital corp', ' energy inc', ' energy corp', ' industries inc', ' systems inc', ' solutions inc', ' resources inc', ' ltd/adr', ' inc/adr',
            ' corp ii', ' co ltd', ' co inc', ' corp /de/', ' trust inc', ' fund inc', ' corporation', ' incorporated', ' companies', ' company', ' l.l.c.', ' inc.', ' corp.', ' ltd.', ' technologies', ' technology', ' inc', ' corp', ' ltd', ' llc', ' plc', ' trust', ' fund', ' co.', ' co', ' sa', ' nv', ' ag', ' /de/', ' lp', ' limited', ' ii', ' i'
        ]
        
        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        normalized = normalized.replace(',', '').replace('.', '').replace('&', 'and')
        normalized = ' '.join(normalized.split())  
        
        return normalized
    
    def get_ticker_from_company_name(self, company_name: str) -> Optional[str]:
        if not company_name:
            return None
        
        normalized_name = self._normalize_company_name(company_name)
        return self.reverse_company_map.get(normalized_name)


ticker_manager = TickerManager()

def is_valid_ticker(ticker: str) -> bool:
    return ticker_manager.is_valid_ticker(ticker)


def get_ticker_from_company_name(company_name: str) -> Optional[str]:
    return ticker_manager.get_ticker_from_company_name(company_name)