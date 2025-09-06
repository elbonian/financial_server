# Real-World Examples

This document contains real examples from actual usage of the Financial Data Server.

## Example 1: NVIDIA 2025 Data Retrieval

### Request
```bash
curl "http://localhost:8000/api/v1/tickers/NVDA/prices?start_date=2025-01-01&end_date=2025-12-31"
```

### Server Logs
```
INFO:financial_server.main:📊 Request: NVDA from 2025-01-01 to 2025-12-31
INFO:financial_server.main:📂 Found 0 existing records in database
INFO:financial_server.main:🔍 Missing 1 date ranges, fetching...
INFO:financial_server.main:📥 Fetching NVDA from 2025-01-01 to 2025-12-31
WARNING:financial_server.data_fetcher:⚠️ ticker_downloader not available: No module named 'ticker_downloader'
INFO:financial_server.data_fetcher:🔄 Trying yfinance directly for NVDA
INFO:financial_server.data_fetcher:✅ Got 145 real records from yfinance direct
INFO:financial_server.database:📥 Inserted 145 records for NVDA
INFO:financial_server.main:✅ Stored 145 new records
INFO:financial_server.main:📤 Returning 145 total records
```

### Response Summary
- **Data Points**: 145 records
- **Date Range**: 2025-01-02 to 2025-08-01
- **Price Range**: $94.30 to $179.27
- **Average Price**: $132.94
- **Data Source**: yfinance_direct
- **File Created**: NVDA_2025_data_20250803_004152.csv (16KB)

### Sample Data
```csv
date,open,high,low,close,volume,source
2025-01-02,135.97804923146714,138.85758927368732,134.608275235204,138.2876739501953,198247200,yfinance_direct
2025-01-03,139.9873988596089,144.87660907201655,139.70744526818353,144.44668579101562,229322500,yfinance_direct
2025-08-01,174.08999633789062,176.5399932861328,170.88999938964844,173.72000122070312,203851100,yfinance_direct
```

### Python Script for CSV Export
```python
#!/usr/bin/env python3
import requests
import csv
from datetime import datetime

def get_nvidia_data():
    # Request data from server
    response = requests.get(
        "http://localhost:8000/api/v1/tickers/NVDA/prices",
        params={"start_date": "2025-01-01", "end_date": "2025-12-31"}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Create CSV file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f'NVDA_2025_data_{timestamp}.csv'
        
        with open(csv_filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'open', 'high', 'low', 'close', 'volume', 'source'])
            writer.writeheader()
            writer.writerows(data['data'])
        
        print(f"✅ Retrieved {data['data_points']} NVIDIA records")
        print(f"📅 Date range: {data['start_date']} to {data['end_date']}")
        print(f"💾 Saved to: {csv_filename}")
        
        # Price analysis
        prices = [float(record['close']) for record in data['data']]
        print(f"💸 Price range: ${min(prices):.2f} to ${max(prices):.2f}")
        print(f"📈 Average price: ${sum(prices)/len(prices):.2f}")
        
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        return False

if __name__ == "__main__":
    get_nvidia_data()
```

### Key Behaviors Demonstrated

1. **No Mock Data**: Server correctly returned only real market data
2. **Partial Range Handling**: Requested full year 2025, got available data (Jan-Aug)
3. **Smart Caching**: Data now cached in SQLite for instant future requests
4. **Source Transparency**: All records clearly marked as `yfinance_direct`
5. **Graceful Fallback**: When ticker_downloader unavailable, used yfinance directly

## Example 2: Cache Hit Performance

### Second Request for Same Data
```bash
curl "http://localhost:8000/api/v1/tickers/NVDA/prices?start_date=2025-07-01&end_date=2025-08-01"
```

### Server Logs (Cache Hit)
```
INFO:financial_server.main:📊 Request: NVDA from 2025-07-01 to 2025-08-01
INFO:financial_server.main:📂 Found 23 existing records in database
INFO:financial_server.utils:✅ No missing dates found - all data available
INFO:financial_server.main:📤 Returning 23 total records
```

**Response Time**: < 50ms (instant cache hit)

## Production Readiness Indicators

✅ **Real Data Only**: No mock data generation  
✅ **Intelligent Caching**: SQLite-based persistence  
✅ **Smart Gap Filling**: Automatic missing data detection  
✅ **Source Tracking**: Clear data provenance  
✅ **Error Handling**: Graceful fallbacks  
✅ **Performance**: Sub-50ms cache hits  
✅ **Data Integrity**: Accurate financial data  