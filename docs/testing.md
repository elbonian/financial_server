# Testing

The test suite has 68 tests covering all functionality.

## Run All Tests

```bash
pytest tests/
```

## Run Specific Tests

```bash
# API tests only
pytest tests/test_api.py

# Database tests only
pytest tests/test_database.py

# Cache-related tests
pytest tests/ -k "cache"
```

## Test Categories

| File | Tests | Coverage |
|------|-------|----------|
| `test_api.py` | 19 | Endpoints, cache hits, error handling |
| `test_data_fetcher.py` | 10 | Data fetching, normalization |
| `test_database.py` | 11 | Database operations, queries |
| `test_utils.py` | 28 | Date utilities, gap detection |

## Key Tests

**Cache Hit Performance**
```python
def test_get_ticker_prices_success_cached_data(self, mock_fetch, temp_db_client):
    """Verifies cached data is served without external API calls"""
    # Pre-populate database
    # Request same data
    # Verify: mock_fetch.assert_not_called()
```

**Smart Gap Filling**
```python
def test_partial_cache_hit_fills_gaps(self, mock_fetch, temp_db_client):
    """Tests that only missing data is fetched"""
    # Cache has Jan 1-2
    # Request Jan 1-4
    # Verify: Only fetches Jan 3-4
```

**No Mock Data**
```python
def test_no_mock_data_when_real_sources_fail(self, data_fetcher):
    """Ensures empty list returned when real sources fail"""
```

## Test Infrastructure

- **Fixtures**: `temp_db_client` creates isolated test database
- **Mocking**: All external API calls mocked (no network dependency)
- **Isolation**: Each test runs with clean database state
- **Speed**: Full suite runs in ~3 seconds

## Adding Tests

1. Test file naming: `test_*.py`
2. Test function naming: `test_<functionality>_<scenario>`
3. Use `temp_db_client` fixture for API tests
4. Always mock external calls
