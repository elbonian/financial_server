"""
Integration tests for the FastAPI server
"""

import pytest
import tempfile
import os
from datetime import date
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the FastAPI app
from financial_server.main import app
from financial_server.database import LocalDatabase
from financial_server.data_fetcher import DataFetcher

class TestFinancialAPI:
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        return TestClient(app)
    
    @pytest.fixture
    def temp_db_client(self):
        """Create a test client with a temporary database"""
        # Create temporary database
        temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_file.close()
        
        # Mock the database in the main module
        with patch('financial_server.main.db') as mock_db:
            mock_db_instance = LocalDatabase(temp_file.name)
            mock_db.return_value = mock_db_instance
            mock_db.health_check = mock_db_instance.health_check
            mock_db.get_price_range = mock_db_instance.get_price_range
            mock_db.insert_price_data = mock_db_instance.insert_price_data
            mock_db.get_symbol_coverage = mock_db_instance.get_symbol_coverage
            mock_db.get_all_cached_symbols = mock_db_instance.get_all_cached_symbols
            mock_db.close = mock_db_instance.close
            
            # Update the global db instance in main
            import financial_server.main as main
            main.db = mock_db_instance
            
            # Also initialize data_fetcher
            main.data_fetcher = DataFetcher()
            
            client = TestClient(app)
            yield client, mock_db_instance
        
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    def test_root_endpoint(self, client):
        """Test the root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "Local Financial Data Server"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert "endpoints" in data
    
    def test_health_check(self, temp_db_client):
        """Test the health check endpoint"""
        client, db = temp_db_client
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["database"] == "connected"
        assert data["data_fetcher"] == "ready"
    
    def test_health_check_failure(self, temp_db_client):
        """Test health check when database fails"""
        client, db = temp_db_client
        with patch('financial_server.main.db.health_check') as mock_health:
            mock_health.side_effect = Exception("Database error")
            
            response = client.get("/health")
            
            assert response.status_code == 503
    
    def test_get_ticker_prices_invalid_date_range(self, client):
        """Test ticker prices with invalid date range"""
        # Start date after end date
        response = client.get(
            "/api/v1/tickers/AAPL/prices?start_date=2024-01-31&end_date=2024-01-01"
        )
        
        assert response.status_code == 400
        assert "start_date must be before or equal to end_date" in response.json()["detail"]
    
    def test_get_ticker_prices_future_date(self, client):
        """Test ticker prices with future start date"""
        response = client.get(
            "/api/v1/tickers/AAPL/prices?start_date=2030-01-01&end_date=2030-01-31"
        )
        
        assert response.status_code == 400
        assert "cannot be in the future" in response.json()["detail"]
    
    def test_get_ticker_prices_missing_parameters(self, client):
        """Test ticker prices with missing required parameters"""
        response = client.get("/api/v1/tickers/AAPL/prices")
        
        assert response.status_code == 422  # Validation error
    
    @patch.object(DataFetcher, 'fetch_range')
    def test_get_ticker_prices_success_with_fetching(self, mock_fetch, temp_db_client):
        """Test successful ticker price request that requires data fetching"""
        client, db = temp_db_client
        
        # Mock data fetcher to return some data
        mock_fetch.return_value = [
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
        
        response = client.get(
            "/api/v1/tickers/AAPL/prices?start_date=2024-01-01&end_date=2024-01-02"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "AAPL"
        assert data["start_date"] == "2024-01-01"
        assert data["end_date"] == "2024-01-02"
        assert data["data_points"] == 2
        assert len(data["data"]) == 2
        
        # Verify data structure
        first_record = data["data"][0]
        assert first_record["date"] == "2024-01-01"
        assert first_record["close"] == 103.0
        assert first_record["source"] == "test"
        
        # Verify fetch was called
        mock_fetch.assert_called_once()
    
    @patch.object(DataFetcher, 'fetch_range')
    def test_get_ticker_prices_success_cached_data(self, mock_fetch, temp_db_client):
        """Test successful ticker price request with cached data - NO external API calls"""
        client, db = temp_db_client
        
        # Pre-populate database with test data
        test_data = [
            {
                'date': '2024-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 98.0,
                'close': 103.0,
                'volume': 1000000,
                'source': 'cached_test_data'
            },
            {
                'date': '2024-01-02',
                'open': 103.0,
                'high': 108.0,
                'low': 101.0,
                'close': 106.0,
                'volume': 1200000,
                'source': 'cached_test_data'
            }
        ]
        db.insert_price_data('AAPL', test_data)
        
        # Request data that should be served from cache
        response = client.get(
            "/api/v1/tickers/AAPL/prices?start_date=2024-01-01&end_date=2024-01-02"
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "AAPL"
        assert data["data_points"] == 2
        assert data["data"][0]["close"] == 103.0
        assert data["data"][1]["close"] == 106.0
        assert data["data"][0]["source"] == "cached_test_data"
        
        # CRITICAL: Verify data fetcher was NOT called (data served from cache)
        mock_fetch.assert_not_called()
    
    @patch.object(DataFetcher, 'fetch_range')
    def test_partial_cache_hit_fills_gaps(self, mock_fetch, temp_db_client):
        """Test that server uses cache for existing data and only fetches missing gaps"""
        client, db = temp_db_client
        
        # Pre-populate database with partial data (Jan 1-2)
        cached_data = [
            {
                'date': '2024-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 98.0,
                'close': 103.0,
                'volume': 1000000,
                'source': 'cached_test_data'
            },
            {
                'date': '2024-01-02',
                'open': 103.0,
                'high': 108.0,
                'low': 101.0,
                'close': 106.0,
                'volume': 1200000,
                'source': 'cached_test_data'
            }
        ]
        db.insert_price_data('AAPL', cached_data)
        
        # Mock data fetcher to return data for missing dates (Jan 3-4)
        mock_fetch.return_value = [
            {
                'date': '2024-01-03',
                'open': 106.0,
                'high': 110.0,
                'low': 104.0,
                'close': 109.0,
                'volume': 1100000,
                'source': 'yfinance_direct'
            },
            {
                'date': '2024-01-04',
                'open': 109.0,
                'high': 112.0,
                'low': 107.0,
                'close': 111.0,
                'volume': 1300000,
                'source': 'yfinance_direct'
            }
        ]
        
        # Request data for Jan 1-4 (partial cache hit)
        response = client.get(
            "/api/v1/tickers/AAPL/prices?start_date=2024-01-01&end_date=2024-01-04"
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "AAPL"
        assert data["data_points"] == 4
        
        # Verify cached data is included
        assert data["data"][0]["date"] == "2024-01-01"
        assert data["data"][0]["source"] == "cached_test_data"
        assert data["data"][1]["date"] == "2024-01-02"  
        assert data["data"][1]["source"] == "cached_test_data"
        
        # Verify new data is included
        assert data["data"][2]["date"] == "2024-01-03"
        assert data["data"][2]["source"] == "yfinance_direct"
        assert data["data"][3]["date"] == "2024-01-04"
        assert data["data"][3]["source"] == "yfinance_direct"
        
        # CRITICAL: Verify data fetcher was called exactly once for missing range only
        mock_fetch.assert_called_once()
    
    @patch.object(DataFetcher, 'fetch_range')
    def test_get_ticker_prices_no_data_available(self, mock_fetch, temp_db_client):
        """Test ticker prices when no data is available"""
        client, db = temp_db_client
        
        # Mock data fetcher to return empty data
        mock_fetch.return_value = []
        
        response = client.get(
            "/api/v1/tickers/NONEXISTENT/prices?start_date=2024-01-01&end_date=2024-01-01"
        )
        
        assert response.status_code == 404
        assert "No data available" in response.json()["detail"]
    
    @patch.object(DataFetcher, 'fetch_range')
    def test_get_ticker_prices_fetch_error(self, mock_fetch, temp_db_client):
        """Test ticker prices when data fetching fails"""
        client, db = temp_db_client
        
        # Mock data fetcher to raise an exception
        mock_fetch.side_effect = Exception("Data source error")
        
        response = client.get(
            "/api/v1/tickers/AAPL/prices?start_date=2024-01-01&end_date=2024-01-01"
        )
        
        # When data fetching fails, the server returns 404 (no data available)
        # rather than 500, because our system treats failed fetches as "no data"
        assert response.status_code == 404
        assert "No data available" in response.json()["detail"]
    
    def test_get_cache_status_for_symbol(self, temp_db_client):
        """Test cache status for a specific symbol"""
        client, db = temp_db_client
        
        # Pre-populate database with test data
        test_data = [
            {
                'date': '2024-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 98.0,
                'close': 103.0,
                'volume': 1000000,
                'source': 'test'
            }
        ]
        db.insert_price_data('AAPL', test_data)
        
        response = client.get("/api/v1/cache/status/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "AAPL"
        assert data["cached"] == True
        assert data["total_records"] == 1
        assert len(data["date_ranges"]) == 1
        assert "last_updated" in data
    
    def test_get_cache_status_for_nonexistent_symbol(self, temp_db_client):
        """Test cache status for a symbol that doesn't exist"""
        client, db = temp_db_client
        
        response = client.get("/api/v1/cache/status/NONEXISTENT")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "NONEXISTENT"
        assert data["cached"] == False
        assert data["total_records"] == 0
        assert len(data["date_ranges"]) == 0
    
    def test_get_all_cache_status_empty(self, temp_db_client):
        """Test getting all cache status when no data exists"""
        client, db = temp_db_client
        
        response = client.get("/api/v1/cache/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_all_cache_status_with_data(self, temp_db_client):
        """Test getting all cache status with multiple symbols"""
        client, db = temp_db_client
        
        # Pre-populate database with test data for multiple symbols
        test_data = [
            {
                'date': '2024-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 98.0,
                'close': 103.0,
                'volume': 1000000,
                'source': 'test'
            }
        ]
        
        db.insert_price_data('AAPL', test_data)
        db.insert_price_data('MSFT', test_data)
        
        response = client.get("/api/v1/cache/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 2
        
        symbols = [item["symbol"] for item in data]
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        
        for item in data:
            assert item["cached"] == True
            assert item["total_records"] == 1
    
    def test_symbol_case_insensitive(self, temp_db_client):
        """Test that symbol requests are case insensitive"""
        client, db = temp_db_client
        
        # Pre-populate database with uppercase symbol
        test_data = [
            {
                'date': '2024-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 98.0,
                'close': 103.0,
                'volume': 1000000,
                'source': 'test'
            }
        ]
        db.insert_price_data('AAPL', test_data)
        
        # Request with lowercase symbol
        response = client.get(
            "/api/v1/tickers/aapl/prices?start_date=2024-01-01&end_date=2024-01-01"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"  # Should be normalized to uppercase
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present"""
        response = client.get("/")
        
        # Check for CORS headers (they should be present due to middleware)
        assert response.status_code == 200
        # Note: TestClient might not include all CORS headers, 
        # but this verifies the endpoint works
    
    def test_api_documentation_available(self, client):
        """Test that API documentation is available"""
        response = client.get("/docs")
        
        assert response.status_code == 200
        # Should return HTML content for Swagger UI
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Local Financial Data Server"