# Financial Data Server

A simple local server for fetching and caching financial market data. Built because I got tired of hitting rate limits on public APIs and wanted something that just works for my own analysis scripts.

## What it does

- Fetches historical price data from Yahoo Finance
- Caches everything in SQLite so repeated requests are instant
- Handles stocks, ETFs, and crypto
- Returns only finalized closing prices (no weird intraday data)
- Can fetch dividend history too

## Quick start

Install and run:

```bash
pip install -e .
python scripts/server.py
```

Then try it out:

```bash
# Get stock prices
curl "http://localhost:8000/api/v1/tickers/AAPL/prices?start_date=2024-01-01&end_date=2024-12-31"

# Get dividend history for an ETF
curl "http://localhost:8000/api/v1/tickers/SCHD/dividends?start_date=2024-01-01&end_date=2024-12-31"

# Get complete historical dataset (from IPO to today)
curl "http://localhost:8000/api/v1/tickers/AAPL/complete"
```

The server runs on `http://localhost:8000`. API docs are at `/docs`.

## Why I built this

Most financial data APIs have annoying limitations:
- Rate limits that kick in right when you're in the middle of analysis
- Expensive paid tiers for historical data
- Give you today's "close" price at 11am (spoiler: it's not actually the close yet)

This server solves those by:
- Caching everything locally (SQLite) - subsequent requests are ~50ms
- Automatically cutting off at yesterday's date during market hours

## How the caching works

The first time you request data for a symbol, it fetches from Yahoo Finance and stores it in `financial_data.db`. After that, requests are served from the local cache instantly.

The server is smart about gaps - if you have Jan-Mar cached but request Jan-Jun, it only fetches April-June from the API.

## One quirk worth knowing

During market hours, Yahoo Finance may return today's date with what looks like a closing price, but it's actually just the current trading price or yesterday's close mislabeled. 

This server automatically adjusts any request that includes "today" to end at yesterday instead. So if you ask for Jan 1 through today (April 25), you get Jan 1 through April 24. This ensures you always get genuine closing prices, not provisional intraday data.

## Running tests

```bash
pip install -e ".[dev]"
pytest tests/
```

68 tests covering the API, data fetching, database, and utilities.

## Project structure

```
financial_server/
├── scripts/server.py      # Entry point
├── src/financial_server/  # Main code
│   ├── main.py           # FastAPI routes
│   ├── data_fetcher.py   # Yahoo Finance integration
│   ├── database.py       # SQLite caching
│   └── models.py         # Pydantic schemas
├── tests/                # Test suite
└── docs/                 # Detailed docs
```

## Documentation

See the [docs/](docs/) directory for:
- Full API reference
- Architecture notes
- Real-world usage examples

## License

MIT - do what you want with it.
