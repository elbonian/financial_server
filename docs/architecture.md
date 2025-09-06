# Financial Data Server Architecture

## Overview

The Financial Data Server is designed as a local server that provides real-time financial data with intelligent caching. It follows a modular architecture with clear separation of concerns.

## Core Components

### 1. API Layer (`main.py`)
- FastAPI application
- RESTful endpoints
- Request/response handling
- Error management

### 2. Data Fetching (`data_fetcher.py`)
- Real-time data retrieval
- Multiple source support:
  - Yahoo Finance (primary)
  - Alpha Vantage (secondary)
- Fallback mechanisms
- Data normalization

### 3. Database Management (`database.py`)
- SQLite database
- Intelligent caching
- Data persistence
- Cache invalidation

### 4. Data Models (`models.py`)
- Pydantic models
- Data validation
- Type checking
- Response formatting

### 5. Utilities (`utils.py`)
- Date handling
- Gap detection
- Range calculations
- Helper functions

## Data Flow

1. Client Request → API Endpoint
2. Check Cache (SQLite)
3. Identify Missing Data
4. Fetch Real-time Data (if needed)
5. Store in Cache
6. Return Response

## Design Decisions

### Why SQLite?
- Single-file database
- No separate server needed
- ACID compliance
- Perfect for local caching

### Why FastAPI?
- Modern, fast framework
- Automatic OpenAPI docs
- Type checking
- Async support

### Why Multiple Data Sources?
- Reliability
- Fallback options
- Different data granularity

## Performance Considerations

- Cache hits < 50ms
- Real-time fetches < 2s
- Smart gap filling
- Efficient date range handling
