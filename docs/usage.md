# Usage Guide

## Data Availability

This server only returns real data from Yahoo Finance. If data isn't available, you get an error instead of fake data.

## Basic Usage

### Get Stock Prices

```bash
curl "http://localhost:8000/api/v1/tickers/AAPL/prices?start_date=2024-01-01&end_date=2024-12-31"
```

The server will:
1. Check the SQLite cache for existing data
2. Download any missing data from Yahoo Finance
3. Cache it for future requests
4. Return the complete dataset

Example response:
```json
{
  "symbol": "AAPL",
  "data_points": 252,
  "start_date": "2024-01-02",
  "end_date": "2024-12-31",
  "data": [
    {
      "date": "2024-01-02",
      "open": 185.0,
      "high": 188.5,
      "low": 184.5,
      "close": 187.5,
      "volume": 52341200,
      "source": "yfinance_direct"
    }
  ]
}
```

### Get Dividend History

```bash
curl "http://localhost:8000/api/v1/tickers/SCHD/dividends?start_date=2024-01-01&end_date=2024-12-31"
```

Example response:
```json
{
  "symbol": "SCHD",
  "data_points": 4,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "data": [
    {"date": "2024-03-20", "amount": 0.203667},
    {"date": "2024-06-26", "amount": 0.274667},
    {"date": "2024-09-25", "amount": 0.251667},
    {"date": "2024-12-11", "amount": 0.265}
  ]
}
```

### Get Complete Historical Dataset

```bash
curl "http://localhost:8000/api/v1/tickers/AAPL/complete"
```

This fetches from IPO to present. First request takes a few seconds. Subsequent requests are instant.

### Check Cache Status

```bash
curl "http://localhost:8000/api/v1/cache/status/AAPL"
```

## Error Handling

**No Data Available (404)**
```bash
curl "http://localhost:8000/api/v1/tickers/INVALID/prices?start_date=2024-01-01&end_date=2024-12-31"
```
Returns: `{"detail": "No data available for INVALID in the requested date range"}`

**Invalid Date Range (400)**
```bash
curl "http://localhost:8000/api/v1/tickers/AAPL/prices?start_date=2025-12-31&end_date=2024-01-01"
```
Returns: `{"detail": "start_date must be before or equal to end_date"}`

## Python Example

```python
import requests

def get_prices(symbol, start_date, end_date):
    url = f"http://localhost:8000/api/v1/tickers/{symbol}/prices"
    params = {"start_date": start_date, "end_date": end_date}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data['data']
    elif response.status_code == 404:
        print("No data available")
        return None
    else:
        print(f"Error: {response.status_code}")
        return None

# Usage
prices = get_prices("AAPL", "2024-01-01", "2024-12-31")
if prices:
    print(f"Got {len(prices)} price records")
```

## Date Handling

The server automatically cuts off at yesterday's date if you request data that includes "today". This prevents getting provisional intraday data mislabeled as closing prices.

**Example:** If today is April 25 and you request Jan 1 to today, you get Jan 1 to April 24.

## Including Today's Data

Use `allow_today=true` to include today's data. This fetches fresh data directly from Yahoo Finance **without caching it**.

```bash
# Get historical data + today's fresh price
curl "http://localhost:8000/api/v1/tickers/AAPL/prices?start_date=2024-01-01&end_date=2025-04-25&allow_today=true"
```

**When to use:**
- After market close (4 PM EST for US stocks) to get the official closing price
- For live dashboards that need current prices during trading hours
- When you know the data you want is available despite the date being "today"

**Response includes:**
```json
{
  "symbol": "AAPL",
  "includes_today_data": true,
  "data_points": 253,
  "data": [...]
}
```

**Important:** The client is responsible for knowing when markets are open. The server doesn't track timezones or market hours.

## Cache Behavior

- First request for a symbol: fetches from Yahoo Finance (1-3 seconds)
- Subsequent requests for cached dates: < 50ms
- Partial cache hit: only fetches missing dates
- No automatic expiration - data persists in `financial_data.db`

## Troubleshooting

**Server not responding?**
```bash
curl http://localhost:8000/health
```

**Want to see what's cached?**
```bash
curl http://localhost:8000/api/v1/cache/status
```

**Need to force refresh complete data?**
```bash
curl "http://localhost:8000/api/v1/tickers/AAPL/complete?force_refresh=true"
```
