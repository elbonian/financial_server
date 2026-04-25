# API Documentation

## Endpoints

### GET /api/v1/tickers/{symbol}/prices

Get historical price data for a financial instrument.

#### Parameters
- `symbol` (path): Ticker symbol (e.g., "BTC-USD", "AAPL")
- `start_date` (query): Start date in YYYY-MM-DD format
- `end_date` (query): End date in YYYY-MM-DD format

#### Success Response (200)
Returns available data within the requested range. The server will:
1. Check cache for existing data
2. Try to download missing data from external sources (yfinance_direct)
3. Return all available data within the requested range
4. Cache new data in SQLite for future requests

```json
{
  "symbol": "NVDA",
  "data_points": 145,
  "start_date": "2025-01-02",  // Actual start of available data
  "end_date": "2025-08-01",    // Actual end of available data (partial year)
  "data": [
    {
      "date": "2025-01-02",
      "open": 135.97804923146714,
      "high": 138.85758927368732,
      "low": 134.608275235204,
      "close": 138.2876739501953,
      "volume": 198247200,
      "source": "yfinance_direct"
    }
  ]
}
```

#### Error Responses

##### No Data Available (404)
When no data is available for the requested symbol and date range:
```json
{
  "error": "No data available",
  "detail": "Could not retrieve data for BTC-USD between 2024-01-01 and 2024-12-31",
  "code": "NO_DATA_AVAILABLE"
}
```

##### Invalid Symbol (404)
When the requested symbol doesn't exist:
```json
{
  "error": "Symbol not found",
  "detail": "Symbol INVALID-SYMBOL does not exist",
  "code": "INVALID_SYMBOL"
}
```

##### Invalid Date Range (400)
When the date range is invalid:
```json
{
  "error": "Invalid date range",
  "detail": "end_date cannot be before start_date",
  "code": "INVALID_DATE_RANGE"
}
```

##### External Service Error (503)
When external data sources are unavailable:
```json
{
  "error": "External service unavailable",
  "detail": "Could not connect to data provider",
  "code": "EXTERNAL_SERVICE_ERROR"
}
```

### GET /api/v1/tickers/{symbol}/dividends

Get historical dividend data for a stock.

**Note**: Not all instruments pay dividends (e.g., growth stocks, ETFs like SCHD do; TSLA, BTC-USD do not).

#### Parameters
- `symbol` (path): Ticker symbol (e.g., "AAPL", "MSFT", "SCHD")
- `start_date` (query): Start date in YYYY-MM-DD format
- `end_date` (query): End date in YYYY-MM-DD format

#### Success Response (200)
Returns dividend payments within the requested date range.

```json
{
  "symbol": "SCHD",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "data_points": 4,
  "data": [
    {
      "date": "2024-03-20",
      "amount": 0.203667
    },
    {
      "date": "2024-06-26",
      "amount": 0.274667
    },
    {
      "date": "2024-09-25",
      "amount": 0.251667
    },
    {
      "date": "2024-12-11",
      "amount": 0.265
    }
  ]
}
```

#### No Dividends Response (200)
When the symbol exists but pays no dividends in the range:

```json
{
  "symbol": "TSLA",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "data_points": 0,
  "data": []
}
```

#### Examples

**Dividend-paying stock (SCHD ETF)**
```bash
curl "http://localhost:8000/api/v1/tickers/SCHD/dividends?start_date=2024-01-01&end_date=2024-12-31"
```

**Quarterly dividend stock (AAPL)**
```bash
curl "http://localhost:8000/api/v1/tickers/AAPL/dividends?start_date=2024-01-01&end_date=2024-12-31"
```

### GET /api/v1/cache/status/{symbol}

Get cache status for a specific symbol.

#### Parameters
- `symbol` (path): Ticker symbol

#### Success Response (200)
```json
{
  "symbol": "BTC-USD",
  "cached_ranges": [
    {
      "start_date": "2024-01-01",
      "end_date": "2024-03-31"
    }
  ],
  "total_records": 90,
  "last_updated": "2025-08-03T00:00:00Z"
}
```

### GET /health

Server health check endpoint.

#### Success Response (200)
```json
{
  "status": "healthy",
  "uptime": "1h 30m",
  "database": "connected",
  "version": "1.0.0"
}
```

## Data Availability

The server follows these principles:
1. **No Mock Data**: The server never generates mock data
2. **Partial Data**: If only part of the requested range is available, returns only that part
3. **Data Sources**: Tries multiple sources in order:
   - Cache (SQLite)
   - Yahoo Finance
   - Alpha Vantage (if API key provided)
4. **Error Reporting**: Clear error messages when data is unavailable

## Examples

### Successful Request (Full Range Available)
```bash
curl "http://localhost:8000/api/v1/tickers/NVDA/prices?start_date=2025-01-01&end_date=2025-12-31"
```
Returns all available data in the range. Server logs show:
```
INFO: Got 145 real records from yfinance direct
INFO: Inserted 145 records for NVDA  
INFO: Returning 145 total records
```

### Successful Request (Partial Range)
When requesting full year 2025 data but only partial year is available:
```json
{
  "symbol": "NVDA",
  "data_points": 145,
  "start_date": "2025-01-02",  // Note: Market closed Jan 1st
  "end_date": "2025-08-01",    // Note: Only through August (current data)
  "data": [
    {
      "date": "2025-08-01",
      "close": 173.72000122070312,
      "source": "yfinance_direct"
    }
  ]
}
```

### Failed Request (No Data)
```bash
curl "http://localhost:8000/api/v1/tickers/INVALID-SYMBOL/prices?start_date=2024-01-01&end_date=2024-03-31"
```
Returns 404 error with clear message.

---

## Complete Dataset Endpoint

### GET /api/v1/tickers/{symbol}/complete

**✨ New Feature**: Download and cache the complete historical dataset for a ticker with smart incremental updates.

#### Parameters
- `symbol` (path): Ticker symbol (e.g., 'AAPL', 'BTC-USD')
- `force_refresh` (query, optional): Force refresh even if complete data exists (default: false)

#### Behavior
- **First request**: Fetches complete historical data from IPO to current date
- **Subsequent requests**: Smart incremental updates (fetches only new data since last update)
- **Force refresh**: Re-downloads complete dataset when `force_refresh=true`

#### Success Response (200)
```json
{
  "symbol": "AAPL",
  "start_date": "1980-12-12",
  "end_date": "2025-08-01", 
  "data_points": 11250,
  "data": [
    {
      "date": "1980-12-12",
      "open": 0.513392865657806,
      "high": 0.515625,
      "low": 0.513392865657806,
      "close": 0.515625,
      "volume": 469033600,
      "source": "yfinance_complete"
    },
    // ... thousands more records to current date
  ]
}
```

#### Smart Caching
The endpoint uses intelligent caching:
- ✅ **Complete dataset marker**: Uses special `yfinance_complete` source to identify complete fetches
- ✅ **Incremental updates**: Only fetches new data since the last cached date
- ✅ **Automatic refresh**: Keeps data current without re-downloading historical data
- ✅ **No date limits**: Client doesn't need to know IPO dates or listing periods

#### Examples

**Get complete Apple dataset (first time)**
```bash
curl "http://localhost:8000/api/v1/tickers/AAPL/complete"
```
*Fetches complete historical data from 1980 to present (11,000+ records)*

**Get complete Apple dataset (subsequent calls)**
```bash
curl "http://localhost:8000/api/v1/tickers/AAPL/complete"
```
*Returns cached data + incremental updates since last fetch*

**Force refresh complete dataset**
```bash
curl "http://localhost:8000/api/v1/tickers/AAPL/complete?force_refresh=true"
```
*Re-downloads complete dataset from scratch*

#### Use Cases
- 📊 **Data analysis**: Get complete price history for backtesting
- 🤖 **Machine learning**: Training models with full historical datasets  
- 📈 **Charting**: Display complete price history without date guessing
- 🔄 **Daily updates**: Automatic incremental data fetching for live applications

#### Performance
- **Initial fetch**: 2-5 seconds for complete dataset (varies by symbol age)
- **Incremental updates**: <1 second (only fetches recent data)
- **Cache hits**: <50ms when no new data available