"""
Pytest configuration and shared fixtures
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import ticker_downloader
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

@pytest.fixture(scope="session")
def temp_directory():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup - remove all files in temp directory
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_price_data():
    """Sample price data for testing"""
    return [
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
        },
        {
            'date': '2024-01-03',
            'open': 106.0,
            'high': 110.0,
            'low': 104.0,
            'close': 108.0,
            'volume': 1100000,
            'source': 'test'
        }
    ]

@pytest.fixture
def sample_ticker_symbols():
    """Sample ticker symbols for testing"""
    return ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'BTC-USD', 'ETH-USD']

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_network: mark test as requiring network access"
    )