"""
Local SQLite database operations for financial data storage
"""

import sqlite3
import logging
from typing import List, Dict, Tuple, Optional
from datetime import date, datetime
from contextlib import contextmanager
import os

logger = logging.getLogger(__name__)

class LocalDatabase:
    """SQLite database manager for financial data"""
    
    def __init__(self, db_path: str = "financial_data.db"):
        """
        Initialize database connection and create tables if needed
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
        logger.info(f"📂 Database initialized: {self.db_path}")
    
    def init_database(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tickers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE NOT NULL,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create price_data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER NOT NULL DEFAULT 0,
                    source TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticker_id) REFERENCES tickers (id),
                    UNIQUE(ticker_id, date, source)
                )
            """)
            
            # Create indexes for fast queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_data_ticker_date 
                ON price_data (ticker_id, date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_data_symbol_date 
                ON price_data (ticker_id, date DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tickers_symbol 
                ON tickers (symbol)
            """)
            
            conn.commit()
            logger.info("✅ Database schema initialized")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def health_check(self) -> bool:
        """Check if database is accessible"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            raise
    
    def get_or_create_ticker(self, symbol: str, name: str = None) -> int:
        """
        Get ticker ID, creating the ticker if it doesn't exist
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL')
            name: Optional ticker name
            
        Returns:
            Ticker ID
        """
        symbol = symbol.upper()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Try to get existing ticker
            cursor.execute("SELECT id FROM tickers WHERE symbol = ?", (symbol,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Create new ticker
            cursor.execute(
                "INSERT INTO tickers (symbol, name) VALUES (?, ?)",
                (symbol, name)
            )
            conn.commit()
            return cursor.lastrowid
    
    def insert_price_data(self, symbol: str, price_data: List[Dict]) -> int:
        """
        Insert price data for a symbol
        
        Args:
            symbol: Ticker symbol
            price_data: List of price records
            
        Returns:
            Number of records inserted
        """
        if not price_data:
            return 0
        
        symbol = symbol.upper()
        ticker_id = self.get_or_create_ticker(symbol)
        
        inserted_count = 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for record in price_data:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO price_data 
                        (ticker_id, date, open, high, low, close, volume, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ticker_id,
                        record['date'],
                        float(record['open']),
                        float(record['high']),
                        float(record['low']),
                        float(record['close']),
                        int(record.get('volume', 0)),
                        record.get('source', 'unknown')
                    ))
                    inserted_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to insert record {record}: {e}")
                    continue
            
            conn.commit()
            logger.info(f"📥 Inserted {inserted_count} records for {symbol}")
        
        return inserted_count
    
    def get_price_range(self, symbol: str, start_date: date, end_date: date) -> List[Dict]:
        """
        Get price data for a symbol within a date range
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            List of price records
        """
        symbol = symbol.upper()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT p.date, p.open, p.high, p.low, p.close, p.volume, p.source
                FROM price_data p
                JOIN tickers t ON p.ticker_id = t.id
                WHERE t.symbol = ? 
                  AND p.date >= ? 
                  AND p.date <= ?
                ORDER BY p.date ASC
            """
            
            cursor.execute(query, (symbol, start_date.isoformat(), end_date.isoformat()))
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_symbol_coverage(self, symbol: str) -> List[Dict]:
        """
        Get date range coverage for a symbol
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            List of date ranges with metadata
        """
        symbol = symbol.upper()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    MIN(p.date) as start_date,
                    MAX(p.date) as end_date,
                    COUNT(*) as record_count,
                    p.source
                FROM price_data p
                JOIN tickers t ON p.ticker_id = t.id
                WHERE t.symbol = ?
                GROUP BY p.source
                ORDER BY start_date ASC
            """
            
            cursor.execute(query, (symbol,))
            rows = cursor.fetchall()
            
            return [
                {
                    'start_date': row['start_date'],
                    'end_date': row['end_date'],
                    'record_count': row['record_count'],
                    'source': row['source']
                }
                for row in rows
            ]
    
    def get_all_cached_symbols(self) -> List[str]:
        """Get list of all symbols that have cached data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT t.symbol
                FROM tickers t
                JOIN price_data p ON t.id = p.ticker_id
                ORDER BY t.symbol
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [row['symbol'] for row in rows]
    
    def get_date_coverage_for_symbol(self, symbol: str) -> List[date]:
        """
        Get all dates that have data for a symbol
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            List of dates with data
        """
        symbol = symbol.upper()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT p.date
                FROM price_data p
                JOIN tickers t ON p.ticker_id = t.id
                WHERE t.symbol = ?
                ORDER BY p.date ASC
            """
            
            cursor.execute(query, (symbol,))
            rows = cursor.fetchall()
            
            return [datetime.strptime(row['date'], '%Y-%m-%d').date() for row in rows]
    
    def delete_symbol_data(self, symbol: str) -> int:
        """
        Delete all data for a symbol (useful for testing)
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Number of records deleted
        """
        symbol = symbol.upper()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get ticker ID
            cursor.execute("SELECT id FROM tickers WHERE symbol = ?", (symbol,))
            result = cursor.fetchone()
            
            if not result:
                return 0
            
            ticker_id = result[0]
            
            # Delete price data
            cursor.execute("DELETE FROM price_data WHERE ticker_id = ?", (ticker_id,))
            deleted_count = cursor.rowcount
            
            # Delete ticker if no price data remains
            cursor.execute("DELETE FROM tickers WHERE id = ?", (ticker_id,))
            
            conn.commit()
            logger.info(f"🗑️ Deleted {deleted_count} records for {symbol}")
        
        return deleted_count
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count tickers
            cursor.execute("SELECT COUNT(*) FROM tickers")
            ticker_count = cursor.fetchone()[0]
            
            # Count total price records
            cursor.execute("SELECT COUNT(*) FROM price_data")
            price_count = cursor.fetchone()[0]
            
            # Get database file size
            file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                'ticker_count': ticker_count,
                'price_record_count': price_count,
                'database_size_bytes': file_size,
                'database_size_mb': round(file_size / 1024 / 1024, 2),
                'database_path': self.db_path
            }
    
    def has_complete_dataset(self, symbol: str) -> bool:
        """
        Check if we have a complete dataset for a symbol.
        Uses source tracking to identify complete fetches.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            True if we have complete dataset cached
        """
        symbol = symbol.upper()
        coverage = self.get_symbol_coverage(symbol)
        
        # Look for sources that indicate complete dataset fetches
        complete_sources = ['yfinance_complete', 'complete_fetch', 'max_history']
        
        for range_info in coverage:
            if range_info['source'] in complete_sources:
                # Check if this complete data has substantial records
                if range_info['record_count'] > 50:  # Reasonable threshold
                    return True
        
        return False
    
    def get_latest_date_for_symbol(self, symbol: str) -> Optional[date]:
        """
        Get the most recent date we have data for a symbol.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Latest date or None if no data
        """
        symbol = symbol.upper()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT MAX(p.date) as latest_date
                FROM price_data p
                JOIN tickers t ON p.ticker_id = t.id
                WHERE t.symbol = ?
            """
            
            cursor.execute(query, (symbol,))
            result = cursor.fetchone()
            
            if result and result['latest_date']:
                return datetime.fromisoformat(result['latest_date']).date()
            
            return None
    
    def get_complete_dataset(self, symbol: str) -> List[Dict]:
        """
        Get all cached data for a symbol (for complete dataset endpoint).
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            All price data records for the symbol
        """
        symbol = symbol.upper()
        
        # Use a very broad date range to get everything
        broad_start = date(1900, 1, 1)
        broad_end = date(2030, 12, 31)
        
        return self.get_price_range(symbol, broad_start, broad_end)

    def close(self):
        """Close database (cleanup method)"""
        # SQLite connections are closed automatically with context manager
        logger.info("📂 Database cleanup completed")