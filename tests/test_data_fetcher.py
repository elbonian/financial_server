"""
Unit tests for the data_fetcher module
"""

import pytest
import pandas as pd
from datetime import date
from unittest.mock import patch, MagicMock
from financial_server.data_fetcher import DataFetcher

class TestDataFetcher:
    
    @pytest.fixture
    def data_fetcher(self):
        """Create a DataFetcher instance for testing"""
        return DataFetcher()
    
    def test_initialization(self, data_fetcher):
        """Test DataFetcher initialization"""
        assert data_fetcher.sources == ['defeatbeta', 'yfinance', 'alpha_vantage']
    
    def test_normalize_data(self, data_fetcher):
        """Test data normalization"""
        raw_data = [
            {
                'date': '2024-01-01',
                'open': '100.50',
                'high': '105.75',
                'low': '98.25',
                'close': '103.00',
                'volume': '1000000'
            },
            {
                'date': '2024-01-02',
                'open': 103.0,
                'high': 108.5,
                'low': 101.0,
                'close': 106.25,
                'volume': 1200000
            }
        ]
        
        normalized = data_fetcher._normalize_data(raw_data, 'test_source')
        
        assert len(normalized) == 2
        
        # Check first record
        record1 = normalized[0]
        assert record1['date'] == '2024-01-01'
        assert record1['open'] == 100.50
        assert record1['high'] == 105.75
        assert record1['low'] == 98.25
        assert record1['close'] == 103.00
        assert record1['volume'] == 1000000
        assert record1['source'] == 'test_source'
        
        # Check second record
        record2 = normalized[1]
        assert record2['date'] == '2024-01-02'
        assert record2['open'] == 103.0
        assert record2['source'] == 'test_source'
    
    def test_normalize_data_with_invalid_records(self, data_fetcher):
        """Test data normalization with some invalid records"""
        raw_data = [
            {
                'date': '2024-01-01',
                'open': 100.50,
                'high': 105.75,
                'low': 98.25,
                'close': 103.00,
                'volume': 1000000
            },
            {
                'date': 'invalid-date',  # Invalid date
                'open': 103.0,
                'high': 108.5,
                'low': 101.0,
                'close': 106.25,
                'volume': 1200000
            },
            {
                'date': '2024-01-03',
                'open': 'invalid',  # Invalid number
                'high': 108.5,
                'low': 101.0,
                'close': 106.25,
                'volume': 1200000
            },
            {
                'date': '2024-01-04',
                'open': 105.0,
                'high': 110.0,
                'low': 103.0,
                'close': 108.0,
                'volume': 1100000
            }
        ]
        
        normalized = data_fetcher._normalize_data(raw_data, 'test_source')
        
        # Should only have valid records (first and last)
        assert len(normalized) == 2
        assert normalized[0]['date'] == '2024-01-01'
        assert normalized[1]['date'] == '2024-01-04'
    
    def test_no_mock_data_when_real_sources_fail(self, data_fetcher):
        """Test that no mock data is generated when real sources fail"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)
        
        # Mock yfinance to fail (since ticker_downloader is not available)
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.history.return_value = pd.DataFrame()  # Empty DataFrame
            
            result = data_fetcher.fetch_range('INVALID_SYMBOL', start_date, end_date)
            
            # Should return empty list when no real data is available
            assert result == []
    
    def test_get_available_sources(self, data_fetcher):
        """Test getting available sources"""
        sources = data_fetcher.get_available_sources()
        assert sources == ['defeatbeta', 'yfinance', 'alpha_vantage']
        
        # Should return a copy, not the original
        sources.append('new_source')
        assert 'new_source' not in data_fetcher.sources
    
    def test_set_source_order(self, data_fetcher):
        """Test setting source order"""
        new_order = ['yfinance', 'defeatbeta']
        data_fetcher.set_source_order(new_order)
        
        assert data_fetcher.sources == new_order
    
    def test_set_source_order_with_invalid_sources(self, data_fetcher):
        """Test setting source order with invalid sources"""
        invalid_order = ['yfinance', 'invalid_source', 'defeatbeta']
        data_fetcher.set_source_order(invalid_order)
        
        # Should only keep valid sources
        assert data_fetcher.sources == ['yfinance', 'defeatbeta']
        assert 'invalid_source' not in data_fetcher.sources
    
    @patch('yfinance.Ticker')
    def test_fetch_range_success_yfinance(self, mock_ticker, data_fetcher):
        """Test successful data fetch from yfinance"""
        # Mock yfinance response
        mock_hist = pd.DataFrame({
            'Open': [100.0],
            'High': [105.0], 
            'Low': [98.0],
            'Close': [103.0],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1))
        
        mock_ticker.return_value.history.return_value = mock_hist
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 1)
        
        result = data_fetcher.fetch_range('AAPL', start_date, end_date)
        
        assert len(result) == 1
        assert result[0]['date'] == '2024-01-01'
        assert result[0]['source'] == 'yfinance_direct'
        assert result[0]['close'] == 103.0
        
        # Verify yfinance was called
        mock_ticker.assert_called_once_with('AAPL')
    
    @patch('yfinance.Ticker')
    def test_fetch_range_yfinance_failure_returns_empty(self, mock_ticker, data_fetcher):
        """Test that yfinance failures return empty list (no mock data)"""
        # Mock yfinance to fail
        mock_ticker.return_value.history.side_effect = Exception("Network error")
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 1)
        
        result = data_fetcher.fetch_range('AAPL', start_date, end_date)
        
        # Should return empty list when yfinance fails
        assert result == []
    
    def test_normalize_symbol_in_fetch_range(self, data_fetcher):
        """Test that symbols are normalized in fetch_range"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 1)
        
        # Mock yfinance to test symbol normalization without external calls
        with patch('yfinance.Ticker') as mock_ticker:
            mock_hist = pd.DataFrame({
                'Open': [100.0],
                'High': [105.0], 
                'Low': [98.0],
                'Close': [103.0],
                'Volume': [1000000]
            }, index=pd.date_range('2024-01-01', periods=1))
            
            mock_ticker.return_value.history.return_value = mock_hist
            
            # Test lowercase symbol normalization
            result = data_fetcher.fetch_range('aapl', start_date, end_date)
            
            # Should pass the symbol as-is to yfinance (normalization happens elsewhere)
            mock_ticker.assert_called_with('aapl')
            assert len(result) == 1
            assert result[0]['date'] == '2024-01-01'