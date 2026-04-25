"""
Data models for the Financial Data Server
"""

from pydantic import BaseModel, Field
from datetime import date
from typing import List, Dict, Any, Optional

class PriceRecord(BaseModel):
    """Individual price record for a single trading day"""
    date: str = Field(..., description="Trading date (YYYY-MM-DD)")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price of the day")
    low: float = Field(..., description="Lowest price of the day")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")
    source: str = Field(..., description="Data source (yfinance, defeatbeta, etc.)")

class PriceDataResponse(BaseModel):
    """Response model for ticker price data"""
    symbol: str = Field(..., description="Ticker symbol")
    start_date: date = Field(..., description="Start date of requested range")
    end_date: date = Field(..., description="End date of requested range")
    data_points: int = Field(..., description="Number of data points returned")
    data: List[PriceRecord] = Field(..., description="Price data records")

class DateRange(BaseModel):
    """Date range with metadata"""
    start_date: str = Field(..., description="Range start date")
    end_date: str = Field(..., description="Range end date")
    record_count: int = Field(..., description="Number of records in this range")
    source: str = Field(..., description="Primary data source for this range")

class CacheStatusResponse(BaseModel):
    """Response model for cache status"""
    symbol: str = Field(..., description="Ticker symbol")
    cached: bool = Field(..., description="Whether any data is cached for this symbol")
    total_records: int = Field(..., description="Total number of cached records")
    date_ranges: List[DateRange] = Field(..., description="Cached date ranges")
    last_updated: str = Field(..., description="Last cache update timestamp")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Check timestamp")
    database: str = Field(..., description="Database status")
    data_fetcher: str = Field(..., description="Data fetcher status")

class ServerInfoResponse(BaseModel):
    """Server information response"""
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    status: str = Field(..., description="Service status")
    endpoints: Dict[str, str] = Field(..., description="Available endpoints")

class DividendRecord(BaseModel):
    """Individual dividend record"""
    date: str = Field(..., description="Dividend date (YYYY-MM-DD)")
    amount: float = Field(..., description="Dividend amount per share")

class DividendResponse(BaseModel):
    """Response model for dividend data"""
    symbol: str = Field(..., description="Ticker symbol")
    start_date: date = Field(..., description="Start date of requested range")
    end_date: date = Field(..., description="End date of requested range")
    data_points: int = Field(..., description="Number of dividend records")
    data: List[DividendRecord] = Field(..., description="Dividend records")