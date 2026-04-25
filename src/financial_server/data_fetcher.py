"""
Data fetcher that integrates with the existing ticker_downloader.py
"""

import sys
import os
import logging
import json
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

# Add parent directory to path to import ticker_downloader
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

logger = logging.getLogger(__name__)

class DataFetcher:
    """Data fetcher that integrates with existing ticker_downloader.py"""
    
    def __init__(self):
        """Initialize the data fetcher"""
        self.sources = ['defeatbeta', 'yfinance', 'alpha_vantage']
        logger.info("📡 DataFetcher initialized")
    
    def fetch_range(self, symbol: str, start_date: date, end_date: date) -> List[Dict]:
        """
        Fetch price data for a symbol and date range using existing ticker_downloader
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD')
            start_date: Start date
            end_date: End date
            
        Returns:
            List of price records in standard format
        """
        try:
            # Import ticker_downloader class
            from ticker_downloader import TickerDownloader
            
            symbol = symbol.upper()
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            logger.info(f"📥 Fetching {symbol} from {start_str} to {end_str}")
            
            # Create downloader instance
            downloader = TickerDownloader()
            
            # Try each data source in order of preference
            for source in self.sources:
                try:
                    logger.info(f"🔄 Trying {source} for {symbol}")
                    
                    if source == 'defeatbeta':
                        data = downloader.download_defeatbeta(symbol)
                    elif source == 'yfinance':
                        data = downloader.download_yfinance(symbol, period="max")
                    elif source == 'alpha_vantage':
                        # For alpha_vantage, we'd need an API key
                        # Skip for now unless API key is provided
                        logger.warning(f"⚠️ Alpha Vantage requires API key, skipping")
                        continue
                    else:
                        continue
                    
                    if data:
                        # Filter data to requested date range
                        filtered_data = self._filter_by_date_range(data, start_date, end_date)
                        if filtered_data:
                            normalized_data = self._normalize_data(filtered_data, source)
                            logger.info(f"✅ Got {len(normalized_data)} records from {source}")
                            return normalized_data
                    
                    logger.warning(f"⚠️ No data from {source} for {symbol}")
                    
                except Exception as e:
                    logger.warning(f"❌ {source} failed for {symbol}: {e}")
                    continue
            
            # If all sources fail, raise an exception
            raise Exception(f"All data sources failed for {symbol}")
            
        except ImportError as e:
            logger.warning(f"⚠️ ticker_downloader not available: {e}")
            # Try yfinance directly as backup
            try:
                import yfinance as yf
                logger.info(f"🔄 Trying yfinance directly for {symbol}")
                
                ticker = yf.Ticker(symbol)
                # Use specific start and end dates instead of periods
                hist = ticker.history(start=start_date, end=end_date + timedelta(days=1))
                
                if not hist.empty:
                    data = []
                    for date, row in hist.iterrows():
                        data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': int(row['Volume']),
                        })
                    
                    # Filter to requested date range
                    filtered_data = self._filter_by_date_range(data, start_date, end_date)
                    if filtered_data:
                        normalized_data = self._normalize_data(filtered_data, 'yfinance_direct')
                        logger.info(f"✅ Got {len(normalized_data)} real records from yfinance direct")
                        return normalized_data
                    
                logger.warning("⚠️ No data from yfinance direct")
                    
            except Exception as yf_error:
                logger.error(f"❌ yfinance direct also failed: {yf_error}")
            
            # NO MOCK DATA - Return empty if no real data available
            logger.warning("⚠️ All real sources failed, no data available for this date range")
            return []
        
        except Exception as e:
            logger.error(f"❌ Error fetching data for {symbol}: {e}")
            # Try yfinance as emergency backup
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                # Emergency fallback: try to get data for requested date range
                hist = ticker.history(start=start_date, end=end_date + timedelta(days=1))
                
                if not hist.empty:
                    data = []
                    for date, row in hist.iterrows():
                        data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': int(row['Volume']),
                        })
                    
                    filtered_data = self._filter_by_date_range(data, start_date, end_date)
                    if filtered_data:
                        normalized_data = self._normalize_data(filtered_data, 'yfinance_emergency')
                        logger.info(f"✅ Emergency yfinance got {len(normalized_data)} real records")
                        return normalized_data
            except:
                pass
                
            raise
    
    def _normalize_data(self, parsed_data: List[Dict], source: str) -> List[Dict]:
        """
        Normalize data from ticker_downloader to our standard format
        
        Args:
            parsed_data: Parsed data from ticker_downloader
            source: Data source name
            
        Returns:
            Normalized data records
        """
        normalized = []
        
        for record in parsed_data:
            try:
                # Ensure all required fields are present and properly typed
                normalized_record = {
                    'date': str(record.get('date', '')),
                    'open': float(record.get('open', 0)),
                    'high': float(record.get('high', 0)),
                    'low': float(record.get('low', 0)),
                    'close': float(record.get('close', 0)),
                    'volume': int(record.get('volume', 0)),
                    'source': source
                }
                
                # Validate that we have a valid date
                if normalized_record['date']:
                    # Try to parse the date to ensure it's valid
                    try:
                        datetime.strptime(normalized_record['date'], '%Y-%m-%d')
                        normalized.append(normalized_record)
                    except ValueError:
                        logger.warning(f"Invalid date format: {normalized_record['date']}")
                        continue
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to normalize record {record}: {e}")
                continue
        
        return normalized
    
    def _filter_by_date_range(self, data: List[Dict], start_date: date, end_date: date) -> List[Dict]:
        """
        Filter data to only include records within the specified date range
        
        Args:
            data: List of data records
            start_date: Start date
            end_date: End date
            
        Returns:
            Filtered data records
        """
        filtered = []
        for record in data:
            try:
                if 'date' in record:
                    record_date = datetime.strptime(str(record['date']), '%Y-%m-%d').date()
                    if start_date <= record_date <= end_date:
                        filtered.append(record)
            except (ValueError, TypeError):
                # Skip records with invalid dates
                continue
        
        return filtered
    

    
    def test_sources(self, symbol: str = "AAPL") -> Dict[str, bool]:
        """
        Test all data sources to see which ones are working
        
        Args:
            symbol: Symbol to test with
            
        Returns:
            Dictionary showing which sources are working
        """
        test_start = date(2024, 1, 1)
        test_end = date(2024, 1, 5)
        
        results = {}
        
        for source in self.sources:
            try:
                data = self.fetch_range(symbol, test_start, test_end)
                results[source] = len(data) > 0
                logger.info(f"✅ {source}: Working ({len(data)} records)")
            except Exception as e:
                results[source] = False
                logger.error(f"❌ {source}: Failed - {e}")
        
        return results
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data sources"""
        return self.sources.copy()
    
    def set_source_order(self, sources: List[str]):
        """
        Set the order of data sources to try
        
        Args:
            sources: List of source names in order of preference
        """
        valid_sources = ['defeatbeta', 'yfinance', 'alpha_vantage']
        self.sources = [s for s in sources if s in valid_sources]
        logger.info(f"📡 Source order updated: {self.sources}")
    
    def fetch_dividends(self, symbol: str, start_date: date, end_date: date) -> List[Dict]:
        """
        Fetch dividend data for a symbol and date range using yfinance
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'MSFT')
            start_date: Start date
            end_date: End date
            
        Returns:
            List of dividend records with date and amount
        """
        try:
            import yfinance as yf
            
            symbol = symbol.upper()
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            logger.info(f"💰 Fetching dividends for {symbol} from {start_str} to {end_str}")
            
            ticker = yf.Ticker(symbol)
            
            # Get all historical dividends (yfinance returns all available)
            dividends = ticker.dividends
            
            if dividends is None or dividends.empty:
                logger.info(f"ℹ️ No dividend data available for {symbol}")
                return []
            
            # Filter to requested date range and convert to list of dicts
            dividend_records = []
            for date_index, amount in dividends.items():
                # Convert timestamp to date
                if hasattr(date_index, 'date'):
                    div_date = date_index.date()
                elif hasattr(date_index, 'to_pydatetime'):
                    div_date = date_index.to_pydatetime().date()
                else:
                    # Parse from string if needed
                    div_date = datetime.strptime(str(date_index)[:10], '%Y-%m-%d').date()
                
                # Filter by date range
                if start_date <= div_date <= end_date:
                    dividend_records.append({
                        'date': div_date.strftime('%Y-%m-%d'),
                        'amount': float(amount)
                    })
            
            # Sort by date
            dividend_records.sort(key=lambda x: x['date'])
            
            logger.info(f"✅ Got {len(dividend_records)} dividend records for {symbol}")
            return dividend_records
            
        except Exception as e:
            logger.error(f"❌ Error fetching dividends for {symbol}: {e}")
            return []