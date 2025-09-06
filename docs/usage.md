# Usage Guide

## Data Availability Principles

The Financial Data Server follows these key principles:

1. **No Mock Data**
   - The server never generates mock/fake data
   - If data isn't available, it returns an error
   - Clear error messages indicate why data is unavailable

2. **Partial Data Handling**
   - If only part of the requested range is available, returns that part
   - Response includes actual date range of available data
   - Metadata shows actual data points count

3. **Data Source Priority**
   ```
   1. Check local cache (SQLite)
   2. Try Yahoo Finance
   3. Try Alpha Vantage (if configured)
   4. Return error if no data available
   ```

## Basic Usage

### 1. Get Stock Prices (Example: NVIDIA)
```bash
# Request NVIDIA 2025 data
curl "http://localhost:8000/api/v1/tickers/NVDA/prices?start_date=2025-01-01&end_date=2025-12-31"

# Server will:
# 1. Check cache for existing data (0 records found)
# 2. Download missing data from yfinance_direct (145 records)
# 3. Cache data in SQLite for future requests
# 4. Return available data (Jan 2 - Aug 1, 2025)
```

Example server logs:
```
INFO: Request: NVDA from 2025-01-01 to 2025-12-31
INFO: Found 0 existing records in database
INFO: Got 145 real records from yfinance direct
INFO: Inserted 145 records for NVDA
INFO: Returning 145 total records
```

### 2. Handle Partial Data
```python
import requests

def get_price_data(symbol, start_date, end_date):
    response = requests.get(
        "http://localhost:8000/api/v1/tickers/BTC-USD/prices",
        params={"start_date": start_date, "end_date": end_date}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Requested range: {start_date} to {end_date}")
        print(f"Available range: {data['start_date']} to {data['end_date']}")
        print(f"Data points: {data['data_points']}")
        return data['data']
    elif response.status_code == 404:
        print("No data available for requested range")
        return None
    else:
        print(f"Error: {response.json()['error']}")
        return None
```

### 3. Check Cache Status
```bash
# Check what data is already cached
curl "http://localhost:8000/api/v1/cache/status/BTC-USD"
```

## Error Handling

### 1. No Data Available
```python
try:
    response = requests.get(url, params=params)
    if response.status_code == 404:
        error = response.json()
        if error['code'] == 'NO_DATA_AVAILABLE':
            print(f"No data available: {error['detail']}")
        elif error['code'] == 'INVALID_SYMBOL':
            print(f"Invalid symbol: {error['detail']}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

### 2. External Service Errors
```python
if response.status_code == 503:
    error = response.json()
    if error['code'] == 'EXTERNAL_SERVICE_ERROR':
        print("Data providers unavailable, try again later")
```

## Best Practices

1. **Check Cache First**
   ```bash
   # Before large requests, check what's cached
   curl "http://localhost:8000/api/v1/cache/status/BTC-USD"
   ```

2. **Handle Partial Data**
   - Always check actual date range in response
   - Compare with requested range
   - Process available data accordingly

3. **Error Handling**
   - Implement proper error handling
   - Check error codes and messages
   - Have fallback behavior for missing data

4. **Date Ranges**
   - Request reasonable date ranges
   - Consider data availability
   - Handle timezone differences

## Troubleshooting

### Common Issues

1. **No Data Available**
   - Verify symbol exists
   - Check date range is valid
   - Ensure external services are accessible

2. **Partial Data**
   - Normal if requesting historical data
   - Check actual date range in response
   - Adjust application logic accordingly

3. **Service Errors**
   - Check server health endpoint
   - Verify internet connection
   - Try again later if external services down

### Debugging Tips

1. **Check Server Health**
   ```bash
   curl "http://localhost:8000/health"
   ```

2. **Verify Cache Status**
   ```bash
   curl "http://localhost:8000/api/v1/cache/status/BTC-USD"
   ```

3. **Test with Known Data**
   ```bash
   # Try recent date ranges first
   curl "http://localhost:8000/api/v1/tickers/BTC-USD/prices?start_date=2024-01-01&end_date=2024-01-31"
   ```