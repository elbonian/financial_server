"""
Utility functions for the Financial Data Server
"""

import logging
from datetime import date, timedelta
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

def identify_missing_ranges(existing_data: List[Dict], start_date: date, end_date: date) -> List[Tuple[date, date]]:
    """
    Identify missing date ranges in existing data that need to be fetched
    
    Args:
        existing_data: List of existing price records from database
        start_date: Requested start date
        end_date: Requested end date
        
    Returns:
        List of (start_date, end_date) tuples representing missing ranges
    """
    if not existing_data:
        # No existing data, need entire range
        return [(start_date, end_date)]
    
    # Get dates that we have data for
    existing_dates = set()
    for record in existing_data:
        if isinstance(record['date'], str):
            from datetime import datetime
            record_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
        else:
            record_date = record['date']
        existing_dates.add(record_date)
    
    # Generate all business days in the requested range (skip weekends)
    # We use business days because stock markets are typically closed on weekends
    all_business_dates = []
    current = start_date
    while current <= end_date:
        # Skip weekends (Saturday=5, Sunday=6)
        if current.weekday() < 5:  # Monday=0, Friday=4
            all_business_dates.append(current)
        current += timedelta(days=1)
    
    # Find missing dates
    missing_dates = []
    for target_date in all_business_dates:
        if target_date not in existing_dates:
            missing_dates.append(target_date)
    
    if not missing_dates:
        logger.info("✅ No missing dates found - all data available")
        return []
    
    # Convert missing dates into continuous ranges
    missing_ranges = []
    if missing_dates:
        # Sort missing dates
        missing_dates.sort()
        
        range_start = missing_dates[0]
        range_end = missing_dates[0]
        
        for i in range(1, len(missing_dates)):
            current_date = missing_dates[i]
            previous_date = missing_dates[i-1]
            
            # If dates are within 3 days of each other, consider them continuous
            # (allows for weekends and single holidays)
            if (current_date - previous_date).days <= 3:
                range_end = current_date
            else:
                # Gap found, save current range and start new one
                missing_ranges.append((range_start, range_end))
                range_start = current_date
                range_end = current_date
        
        # Add the final range
        missing_ranges.append((range_start, range_end))
    
    logger.info(f"🔍 Found {len(missing_ranges)} missing date ranges covering {len(missing_dates)} dates")
    for i, (start, end) in enumerate(missing_ranges):
        logger.info(f"  Range {i+1}: {start} to {end}")
    
    return missing_ranges

def validate_date_range(start_date: date, end_date: date) -> bool:
    """
    Validate that a date range is reasonable
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        True if valid, False otherwise
    """
    if start_date > end_date:
        return False
    
    if start_date > date.today():
        return False
    
    # Check if range is reasonable (not too far in the past)
    earliest_reasonable = date(1970, 1, 1)  # Unix epoch
    if start_date < earliest_reasonable:
        return False
    
    # Check if range is not too large (more than 50 years)
    max_range_days = 365 * 50
    if (end_date - start_date).days > max_range_days:
        return False
    
    return True

def normalize_symbol(symbol: str) -> str:
    """
    Normalize a ticker symbol for consistent storage
    
    Args:
        symbol: Raw ticker symbol
        
    Returns:
        Normalized symbol (uppercase, trimmed)
    """
    if not symbol:
        return ""
    
    return symbol.strip().upper()

def format_currency(value: float, decimals: int = 2) -> str:
    """
    Format a currency value for display
    
    Args:
        value: Numeric value
        decimals: Number of decimal places
        
    Returns:
        Formatted string
    """
    return f"${value:,.{decimals}f}"

def calculate_business_days(start_date: date, end_date: date) -> int:
    """
    Calculate number of business days between two dates
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Number of business days
    """
    business_day_count = 0
    current = start_date
    
    while current <= end_date:
        # Count weekdays only (Monday=0, Friday=4)
        if current.weekday() < 5:
            business_day_count += 1
        current += timedelta(days=1)
    
    return business_day_count

def get_date_range_info(start_date: date, end_date: date) -> Dict:
    """
    Get information about a date range
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Dictionary with range information
    """
    total_days = (end_date - start_date).days + 1
    business_days = calculate_business_days(start_date, end_date)
    
    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_days': total_days,
        'business_days': business_days,
        'weekend_days': total_days - business_days,
        'duration_years': round(total_days / 365.25, 2)
    }

def merge_overlapping_ranges(ranges: List[Tuple[date, date]]) -> List[Tuple[date, date]]:
    """
    Merge overlapping date ranges
    
    Args:
        ranges: List of (start_date, end_date) tuples
        
    Returns:
        List of merged ranges
    """
    if not ranges:
        return []
    
    # Sort ranges by start date
    sorted_ranges = sorted(ranges, key=lambda x: x[0])
    merged = [sorted_ranges[0]]
    
    for current_start, current_end in sorted_ranges[1:]:
        last_start, last_end = merged[-1]
        
        # If ranges overlap or are adjacent, merge them
        if current_start <= last_end + timedelta(days=1):
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))
    
    return merged

def chunk_date_range(start_date: date, end_date: date, max_chunk_days: int = 365) -> List[Tuple[date, date]]:
    """
    Split a large date range into smaller chunks for processing
    
    Args:
        start_date: Start date
        end_date: End date
        max_chunk_days: Maximum days per chunk
        
    Returns:
        List of date range chunks
    """
    chunks = []
    current_start = start_date
    
    while current_start <= end_date:
        chunk_end = min(current_start + timedelta(days=max_chunk_days - 1), end_date)
        chunks.append((current_start, chunk_end))
        current_start = chunk_end + timedelta(days=1)
    
    return chunks

def adjust_end_date_for_data_quality(end_date: date) -> date:
    """
    Adjust end date to exclude today to ensure only finalized closing prices are returned.
    
    This prevents returning provisional intraday data that might be mislabeled as 
    closing prices when markets are still open.
    
    Args:
        end_date: Requested end date
        
    Returns:
        Adjusted end date (yesterday if original end date was today or later)
    """
    today = date.today()
    if end_date >= today:
        return today - timedelta(days=1)
    return end_date