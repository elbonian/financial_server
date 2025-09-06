"""
Unit tests for the database module
"""

import pytest
import tempfile
import os
from datetime import date
from financial_server.database import LocalDatabase

class TestLocalDatabase:
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_file.close()
        
        db = LocalDatabase(temp_file.name)
        yield db
        
        # Cleanup
        db.close()
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    def test_database_initialization(self, temp_db):
        """Test that database initializes correctly"""
        assert temp_db.health_check() == True
        
        # Check that tables were created
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'tickers' in tables
            assert 'price_data' in tables
    
    def test_get_or_create_ticker(self, temp_db):
        """Test ticker creation and retrieval"""
        # Create new ticker
        ticker_id1 = temp_db.get_or_create_ticker('AAPL', 'Apple Inc.')
        assert ticker_id1 > 0
        
        # Get existing ticker
        ticker_id2 = temp_db.get_or_create_ticker('AAPL')
        assert ticker_id1 == ticker_id2
        
        # Case insensitive
        ticker_id3 = temp_db.get_or_create_ticker('aapl')
        assert ticker_id1 == ticker_id3
    
    def test_insert_and_retrieve_price_data(self, temp_db):
        """Test inserting and retrieving price data"""
        # Sample price data
        sample_data = [
            {
                'date': '2024-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 98.0,
                'close': 103.0,
                'volume': 1000000,
                'source': 'test'
            },
            {
                'date': '2024-01-02',
                'open': 103.0,
                'high': 108.0,
                'low': 101.0,
                'close': 106.0,
                'volume': 1200000,
                'source': 'test'
            }
        ]
        
        # Insert data
        count = temp_db.insert_price_data('AAPL', sample_data)
        assert count == 2
        
        # Retrieve data
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 2)
        retrieved_data = temp_db.get_price_range('AAPL', start_date, end_date)
        
        assert len(retrieved_data) == 2
        assert retrieved_data[0]['date'] == '2024-01-01'
        assert retrieved_data[0]['close'] == 103.0
        assert retrieved_data[1]['date'] == '2024-01-02'
        assert retrieved_data[1]['close'] == 106.0
    
    def test_get_price_range_empty(self, temp_db):
        """Test retrieving data when none exists"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        data = temp_db.get_price_range('NONEXISTENT', start_date, end_date)
        assert data == []
    
    def test_get_symbol_coverage(self, temp_db):
        """Test getting symbol coverage information"""
        # Insert test data
        sample_data = [
            {'date': '2024-01-01', 'open': 100, 'high': 105, 'low': 98, 'close': 103, 'volume': 1000, 'source': 'test1'},
            {'date': '2024-01-02', 'open': 103, 'high': 108, 'low': 101, 'close': 106, 'volume': 1200, 'source': 'test1'},
            {'date': '2024-01-03', 'open': 106, 'high': 110, 'low': 104, 'close': 108, 'volume': 1100, 'source': 'test2'},
        ]
        
        temp_db.insert_price_data('AAPL', sample_data)
        
        # Get coverage
        coverage = temp_db.get_symbol_coverage('AAPL')
        
        assert len(coverage) == 2  # Two different sources
        
        # Check that both sources are represented
        sources = [c['source'] for c in coverage]
        assert 'test1' in sources
        assert 'test2' in sources
    
    def test_get_all_cached_symbols(self, temp_db):
        """Test getting all symbols with data"""
        # Insert data for multiple symbols
        sample_data = [
            {'date': '2024-01-01', 'open': 100, 'high': 105, 'low': 98, 'close': 103, 'volume': 1000, 'source': 'test'}
        ]
        
        temp_db.insert_price_data('AAPL', sample_data)
        temp_db.insert_price_data('MSFT', sample_data)
        temp_db.insert_price_data('GOOGL', sample_data)
        
        symbols = temp_db.get_all_cached_symbols()
        
        assert len(symbols) == 3
        assert 'AAPL' in symbols
        assert 'MSFT' in symbols
        assert 'GOOGL' in symbols
    
    def test_get_date_coverage_for_symbol(self, temp_db):
        """Test getting date coverage for a symbol"""
        sample_data = [
            {'date': '2024-01-01', 'open': 100, 'high': 105, 'low': 98, 'close': 103, 'volume': 1000, 'source': 'test'},
            {'date': '2024-01-03', 'open': 103, 'high': 108, 'low': 101, 'close': 106, 'volume': 1200, 'source': 'test'},
            {'date': '2024-01-05', 'open': 106, 'high': 110, 'low': 104, 'close': 108, 'volume': 1100, 'source': 'test'},
        ]
        
        temp_db.insert_price_data('AAPL', sample_data)
        
        dates = temp_db.get_date_coverage_for_symbol('AAPL')
        
        assert len(dates) == 3
        assert date(2024, 1, 1) in dates
        assert date(2024, 1, 3) in dates
        assert date(2024, 1, 5) in dates
        assert date(2024, 1, 2) not in dates  # Missing date
    
    def test_delete_symbol_data(self, temp_db):
        """Test deleting all data for a symbol"""
        # Insert test data
        sample_data = [
            {'date': '2024-01-01', 'open': 100, 'high': 105, 'low': 98, 'close': 103, 'volume': 1000, 'source': 'test'}
        ]
        
        temp_db.insert_price_data('AAPL', sample_data)
        temp_db.insert_price_data('MSFT', sample_data)
        
        # Verify data exists
        symbols_before = temp_db.get_all_cached_symbols()
        assert 'AAPL' in symbols_before
        assert 'MSFT' in symbols_before
        
        # Delete AAPL data
        deleted_count = temp_db.delete_symbol_data('AAPL')
        assert deleted_count == 1
        
        # Verify AAPL is gone but MSFT remains
        symbols_after = temp_db.get_all_cached_symbols()
        assert 'AAPL' not in symbols_after
        assert 'MSFT' in symbols_after
    
    def test_get_database_stats(self, temp_db):
        """Test getting database statistics"""
        # Insert some test data
        sample_data = [
            {'date': '2024-01-01', 'open': 100, 'high': 105, 'low': 98, 'close': 103, 'volume': 1000, 'source': 'test'}
        ]
        
        temp_db.insert_price_data('AAPL', sample_data)
        temp_db.insert_price_data('MSFT', sample_data)
        
        stats = temp_db.get_database_stats()
        
        assert 'ticker_count' in stats
        assert 'price_record_count' in stats
        assert 'database_size_bytes' in stats
        assert 'database_size_mb' in stats
        assert 'database_path' in stats
        
        assert stats['ticker_count'] == 2
        assert stats['price_record_count'] == 2
        assert stats['database_size_bytes'] > 0
    
    def test_duplicate_data_handling(self, temp_db):
        """Test that duplicate data is handled correctly"""
        sample_data = [
            {'date': '2024-01-01', 'open': 100, 'high': 105, 'low': 98, 'close': 103, 'volume': 1000, 'source': 'test'}
        ]
        
        # Insert same data twice
        count1 = temp_db.insert_price_data('AAPL', sample_data)
        count2 = temp_db.insert_price_data('AAPL', sample_data)
        
        assert count1 == 1
        assert count2 == 1  # Should still insert (REPLACE)
        
        # Should only have one record
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 1)
        data = temp_db.get_price_range('AAPL', start_date, end_date)
        assert len(data) == 1
    
    def test_invalid_data_handling(self, temp_db):
        """Test handling of invalid data"""
        # Data with missing required fields
        invalid_data = [
            {'date': '2024-01-01', 'open': 'invalid', 'high': 105, 'low': 98, 'close': 103, 'volume': 1000, 'source': 'test'},
            {'date': '2024-01-02', 'open': 100, 'high': 105, 'low': 98, 'close': 103, 'volume': 'invalid', 'source': 'test'},
        ]
        
        # Should skip invalid records but continue with valid ones
        count = temp_db.insert_price_data('AAPL', invalid_data)
        assert count == 0  # Both records should fail due to type conversion errors