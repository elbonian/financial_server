"""
Local Financial Data Server
Simple FastAPI server for serving historical financial data with SQLite storage
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime
from typing import List, Dict, Optional
import logging
from contextlib import asynccontextmanager

from .database import LocalDatabase
from .data_fetcher import DataFetcher
from .models import PriceDataResponse, CacheStatusResponse, ErrorResponse
from .utils import identify_missing_ranges

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
db = None
data_fetcher = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup for the application"""
    global db, data_fetcher
    
    # Startup
    logger.info("🚀 Starting Local Financial Data Server...")
    db = LocalDatabase()
    data_fetcher = DataFetcher()
    logger.info("✅ Server initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down server...")
    if db:
        db.close()

# Create FastAPI app
app = FastAPI(
    title="Local Financial Data Server",
    description="Simple API for serving historical financial data with smart caching",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local use
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with basic server info"""
    return {
        "service": "Local Financial Data Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "prices": "/api/v1/tickers/{symbol}/prices",
            "complete": "/api/v1/tickers/{symbol}/complete",
            "cache_status": "/api/v1/cache/status/{symbol}",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.health_check()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "data_fetcher": "ready"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/api/v1/tickers/{symbol}/prices", response_model=PriceDataResponse)
async def get_ticker_prices(
    symbol: str,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
) -> PriceDataResponse:
    """
    Get price data for a ticker symbol within a date range.
    Automatically fetches and caches missing data.
    
    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD')
        start_date: Start date for data range
        end_date: End date for data range
    
    Returns:
        Complete price data for the requested range
    """
    try:
        # Validate inputs
        if start_date > end_date:
            raise HTTPException(
                status_code=400, 
                detail="start_date must be before or equal to end_date"
            )
        
        if start_date > date.today():
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be in the future"
            )
        
        # Normalize symbol (uppercase)
        symbol = symbol.upper()
        
        logger.info(f"📊 Request: {symbol} from {start_date} to {end_date}")
        
        # 1. Check what we have in database
        existing_data = db.get_price_range(symbol, start_date, end_date)
        logger.info(f"📂 Found {len(existing_data)} existing records in database")
        
        # 2. Identify missing date ranges
        missing_ranges = identify_missing_ranges(existing_data, start_date, end_date)
        
        if missing_ranges:
            logger.info(f"🔍 Missing {len(missing_ranges)} date ranges, fetching...")
            
            # 3. Fetch missing data
            for range_start, range_end in missing_ranges:
                logger.info(f"📥 Fetching {symbol} from {range_start} to {range_end}")
                try:
                    new_data = data_fetcher.fetch_range(symbol, range_start, range_end)
                    if new_data:
                        db.insert_price_data(symbol, new_data)
                        logger.info(f"✅ Stored {len(new_data)} new records")
                    else:
                        logger.warning(f"⚠️ No data returned for {symbol} {range_start}-{range_end}")
                except Exception as e:
                    logger.error(f"❌ Failed to fetch {symbol} {range_start}-{range_end}: {e}")
                    # Continue with other ranges, don't fail entire request
        
        # 4. Get complete data from database
        complete_data = db.get_price_range(symbol, start_date, end_date)
        logger.info(f"📤 Returning {len(complete_data)} total records")
        
        if not complete_data:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for {symbol} in the requested date range"
            )
        
        return PriceDataResponse(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            data_points=len(complete_data),
            data=complete_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/tickers/{symbol}/complete", response_model=PriceDataResponse)
async def get_complete_ticker_data(
    symbol: str,
    force_refresh: bool = Query(False, description="Force refresh even if complete data exists")
) -> PriceDataResponse:
    """
    Download and cache the complete historical dataset for a ticker.
    Uses smart incremental updates to keep data current.
    
    Args:
        symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD')
        force_refresh: Force refresh even if complete data exists
    
    Returns:
        Complete historical price data for the ticker
    """
    try:
        symbol = symbol.upper()
        logger.info(f"📊 Complete dataset request for {symbol} (force_refresh={force_refresh})")
        
        # Check if we already have complete data (unless force_refresh)
        if not force_refresh and db.has_complete_dataset(symbol):
            logger.info(f"✅ Found existing complete dataset for {symbol}, doing incremental update")
            
            # Get latest date in our database
            latest_date = db.get_latest_date_for_symbol(symbol)
            
            if latest_date:
                # Calculate incremental range (latest + 1 day to today)
                from datetime import timedelta
                incremental_start = latest_date + timedelta(days=1)
                incremental_end = date.today()
                
                if incremental_start <= incremental_end:
                    logger.info(f"🔄 Fetching incremental data from {incremental_start} to {incremental_end}")
                    try:
                        incremental_data = data_fetcher.fetch_range(symbol, incremental_start, incremental_end)
                        if incremental_data:
                            db.insert_price_data(symbol, incremental_data)
                            logger.info(f"✅ Added {len(incremental_data)} incremental records")
                        else:
                            logger.info("ℹ️ No new data available for incremental update")
                    except Exception as e:
                        logger.warning(f"⚠️ Incremental update failed: {e}, continuing with cached data")
                else:
                    logger.info("ℹ️ Data is already up to date")
            
            # Return complete dataset (cached + any incremental updates)
            complete_data = db.get_complete_dataset(symbol)
            
        else:
            # No complete dataset exists or force refresh requested
            action = "force refresh" if force_refresh else "initial complete fetch"
            logger.info(f"🔄 Performing {action} for {symbol}")
            
            complete_data = await fetch_complete_dataset(symbol)
            
            if complete_data:
                # Clear existing data and insert fresh complete dataset
                if db.has_complete_dataset(symbol):
                    db.delete_symbol_data(symbol)
                    logger.info(f"🗑️ Cleared existing data for refresh")
                
                db.insert_price_data(symbol, complete_data)
                logger.info(f"✅ Cached {len(complete_data)} complete records")
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"No complete data available for {symbol}"
                )
        
        if not complete_data:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for {symbol}"
            )
        
        # Determine actual date range from the data
        dates = [datetime.fromisoformat(record['date']).date() for record in complete_data]
        actual_start = min(dates)
        actual_end = max(dates)
        
        logger.info(f"📤 Returning {len(complete_data)} complete records ({actual_start} to {actual_end})")
        
        return PriceDataResponse(
            symbol=symbol,
            start_date=actual_start,
            end_date=actual_end,
            data_points=len(complete_data),
            data=complete_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing complete data request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def fetch_complete_dataset(symbol: str) -> List[Dict]:
    """
    Fetch the complete historical dataset for a symbol using yfinance max period.
    Marks the data with special source to indicate completeness.
    
    Args:
        symbol: Ticker symbol
        
    Returns:
        Complete dataset or empty list if failed
    """
    try:
        import yfinance as yf
        logger.info(f"🔄 Fetching complete dataset from yfinance for {symbol}")
        
        ticker = yf.Ticker(symbol)
        # Use period="max" to get complete historical data
        hist = ticker.history(period="max")
        
        if not hist.empty:
            data = []
            for date_index, row in hist.iterrows():
                data.append({
                    'date': date_index.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']),
                })
            
            # Use the existing normalization logic with special source
            normalized_data = data_fetcher._normalize_data(data, 'yfinance_complete')
            logger.info(f"✅ Got {len(normalized_data)} complete records from yfinance")
            return normalized_data
        else:
            logger.warning("⚠️ No complete data from yfinance")
            return []
            
    except Exception as e:
        logger.error(f"❌ Failed to fetch complete dataset: {e}")
        return []

@app.get("/api/v1/cache/status/{symbol}", response_model=CacheStatusResponse)
async def get_cache_status(symbol: str) -> CacheStatusResponse:
    """
    Get cache status for a ticker symbol - shows what date ranges are available.
    
    Args:
        symbol: Ticker symbol to check
        
    Returns:
        Cache coverage information for the symbol
    """
    try:
        symbol = symbol.upper()
        logger.info(f"📋 Cache status request for {symbol}")
        
        coverage = db.get_symbol_coverage(symbol)
        
        return CacheStatusResponse(
            symbol=symbol,
            cached=len(coverage) > 0,
            total_records=sum(r['record_count'] for r in coverage),
            date_ranges=coverage,
            last_updated=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache status: {str(e)}")

@app.get("/api/v1/cache/status", response_model=List[CacheStatusResponse])
async def get_all_cache_status() -> List[CacheStatusResponse]:
    """Get cache status for all cached symbols"""
    try:
        logger.info("📋 All cache status request")
        
        all_symbols = db.get_all_cached_symbols()
        results = []
        
        for symbol in all_symbols:
            coverage = db.get_symbol_coverage(symbol)
            results.append(CacheStatusResponse(
                symbol=symbol,
                cached=True,
                total_records=sum(r['record_count'] for r in coverage),
                date_ranges=coverage,
                last_updated=datetime.now().isoformat()
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error getting all cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache status: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Local Financial Data Server...")
    print("📊 Server will be available at: http://localhost:8000")
    print("📚 API docs: http://localhost:8000/docs")
    print("❤️ Health check: http://localhost:8000/health")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )