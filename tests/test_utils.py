"""
Unit tests for the utils module
"""

import pytest
from datetime import date, timedelta
from financial_server.utils import (
    identify_missing_ranges, 
    validate_date_range, 
    normalize_symbol,
    calculate_business_days,
    get_date_range_info,
    merge_overlapping_ranges,
    chunk_date_range
)

class TestIdentifyMissingRanges:
    
    def test_no_existing_data(self):
        """Test when no existing data exists"""
        existing_data = []
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 10)
        
        missing = identify_missing_ranges(existing_data, start_date, end_date)
        
        assert len(missing) == 1
        assert missing[0] == (start_date, end_date)
    
    def test_complete_data_coverage(self):
        """Test when all data exists"""
        existing_data = [
            {'date': '2024-01-01'},
            {'date': '2024-01-02'},
            {'date': '2024-01-03'},
            {'date': '2024-01-04'},
            {'date': '2024-01-05'},
        ]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)
        
        missing = identify_missing_ranges(existing_data, start_date, end_date)
        
        # Should have no missing ranges (or only weekend gaps which are acceptable)
        assert len(missing) == 0 or all(
            (end - start).days <= 2 for start, end in missing
        )
    
    def test_partial_data_coverage(self):
        """Test when some data is missing"""
        existing_data = [
            {'date': '2024-01-01'},
            {'date': '2024-01-02'},
            # Missing 2024-01-03, 2024-01-04, 2024-01-05
            {'date': '2024-01-08'},
            {'date': '2024-01-09'},
        ]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 10)
        
        missing = identify_missing_ranges(existing_data, start_date, end_date)
        
        assert len(missing) >= 1
        # Should identify the gap between Jan 2 and Jan 8
    
    def test_single_missing_day(self):
        """Test when only one day is missing"""
        existing_data = [
            {'date': '2024-01-01'},
            {'date': '2024-01-02'},
            # Missing 2024-01-03
            {'date': '2024-01-04'},
            {'date': '2024-01-05'},
        ]
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)
        
        missing = identify_missing_ranges(existing_data, start_date, end_date)
        
        # Should identify the single missing day
        assert len(missing) >= 1

class TestValidateDateRange:
    
    def test_valid_range(self):
        """Test valid date range"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        assert validate_date_range(start, end) == True
    
    def test_start_after_end(self):
        """Test invalid range where start is after end"""
        start = date(2024, 1, 31)
        end = date(2024, 1, 1)
        assert validate_date_range(start, end) == False
    
    def test_future_start_date(self):
        """Test invalid range with future start date"""
        tomorrow = date.today() + timedelta(days=1)
        end = tomorrow + timedelta(days=10)
        assert validate_date_range(tomorrow, end) == False
    
    def test_too_old_start_date(self):
        """Test invalid range with very old start date"""
        start = date(1960, 1, 1)
        end = date(1960, 12, 31)
        assert validate_date_range(start, end) == False
    
    def test_too_large_range(self):
        """Test invalid range that's too large"""
        start = date(1980, 1, 1)
        end = date(2040, 12, 31)  # More than 50 years
        assert validate_date_range(start, end) == False
    
    def test_same_date_range(self):
        """Test valid range where start equals end"""
        same_date = date(2024, 1, 1)
        assert validate_date_range(same_date, same_date) == True

class TestNormalizeSymbol:
    
    def test_lowercase_symbol(self):
        """Test normalizing lowercase symbol"""
        assert normalize_symbol('aapl') == 'AAPL'
    
    def test_mixed_case_symbol(self):
        """Test normalizing mixed case symbol"""
        assert normalize_symbol('AaPl') == 'AAPL'
    
    def test_uppercase_symbol(self):
        """Test already uppercase symbol"""
        assert normalize_symbol('AAPL') == 'AAPL'
    
    def test_symbol_with_spaces(self):
        """Test symbol with spaces"""
        assert normalize_symbol(' AAPL ') == 'AAPL'
    
    def test_empty_symbol(self):
        """Test empty symbol"""
        assert normalize_symbol('') == ''
        assert normalize_symbol(None) == ''
    
    def test_crypto_symbol(self):
        """Test cryptocurrency symbol"""
        assert normalize_symbol('btc-usd') == 'BTC-USD'

class TestCalculateBusinessDays:
    
    def test_weekdays_only(self):
        """Test range with only weekdays"""
        start = date(2024, 1, 1)  # Monday
        end = date(2024, 1, 5)    # Friday
        days = calculate_business_days(start, end)
        assert days == 5
    
    def test_including_weekend(self):
        """Test range including weekend"""
        start = date(2024, 1, 1)  # Monday
        end = date(2024, 1, 7)    # Sunday
        days = calculate_business_days(start, end)
        assert days == 5  # Should exclude Saturday and Sunday
    
    def test_single_day(self):
        """Test single day range"""
        single_day = date(2024, 1, 1)  # Monday
        days = calculate_business_days(single_day, single_day)
        assert days == 1
    
    def test_weekend_only(self):
        """Test weekend only range"""
        saturday = date(2024, 1, 6)
        sunday = date(2024, 1, 7)
        days = calculate_business_days(saturday, sunday)
        assert days == 0

class TestGetDateRangeInfo:
    
    def test_date_range_info(self):
        """Test getting date range information"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        
        info = get_date_range_info(start, end)
        
        assert 'start_date' in info
        assert 'end_date' in info
        assert 'total_days' in info
        assert 'business_days' in info
        assert 'weekend_days' in info
        assert 'duration_years' in info
        
        assert info['start_date'] == '2024-01-01'
        assert info['end_date'] == '2024-01-31'
        assert info['total_days'] == 31
        assert info['business_days'] > 0
        assert info['weekend_days'] >= 0

class TestMergeOverlappingRanges:
    
    def test_no_ranges(self):
        """Test empty range list"""
        assert merge_overlapping_ranges([]) == []
    
    def test_non_overlapping_ranges(self):
        """Test non-overlapping ranges"""
        ranges = [
            (date(2024, 1, 1), date(2024, 1, 5)),
            (date(2024, 1, 10), date(2024, 1, 15)),
        ]
        merged = merge_overlapping_ranges(ranges)
        assert len(merged) == 2
        assert merged == ranges
    
    def test_overlapping_ranges(self):
        """Test overlapping ranges"""
        ranges = [
            (date(2024, 1, 1), date(2024, 1, 10)),
            (date(2024, 1, 5), date(2024, 1, 15)),
        ]
        merged = merge_overlapping_ranges(ranges)
        assert len(merged) == 1
        assert merged[0] == (date(2024, 1, 1), date(2024, 1, 15))
    
    def test_adjacent_ranges(self):
        """Test adjacent ranges"""
        ranges = [
            (date(2024, 1, 1), date(2024, 1, 5)),
            (date(2024, 1, 6), date(2024, 1, 10)),
        ]
        merged = merge_overlapping_ranges(ranges)
        assert len(merged) == 1
        assert merged[0] == (date(2024, 1, 1), date(2024, 1, 10))

class TestChunkDateRange:
    
    def test_small_range(self):
        """Test range smaller than chunk size"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 10)
        chunks = chunk_date_range(start, end, max_chunk_days=365)
        
        assert len(chunks) == 1
        assert chunks[0] == (start, end)
    
    def test_large_range(self):
        """Test range larger than chunk size"""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)  # Full year
        chunks = chunk_date_range(start, end, max_chunk_days=100)
        
        assert len(chunks) > 1
        
        # Verify chunks cover the entire range
        assert chunks[0][0] == start
        assert chunks[-1][1] == end
        
        # Verify chunks are contiguous
        for i in range(len(chunks) - 1):
            current_end = chunks[i][1]
            next_start = chunks[i + 1][0]
            assert (next_start - current_end).days == 1
    
    def test_exact_chunk_size(self):
        """Test range that exactly matches chunk size"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 10)  # 10 days
        chunks = chunk_date_range(start, end, max_chunk_days=10)
        
        assert len(chunks) == 1
        assert chunks[0] == (start, end)