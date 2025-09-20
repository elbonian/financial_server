"""
Tests for the date adjustment functionality that ensures data quality
by excluding today's provisional data.
"""

import pytest
from datetime import date, timedelta
from src.financial_server.utils import adjust_end_date_for_data_quality


class TestDateAdjustment:
    """Test the date adjustment logic for data quality"""
    
    def test_adjust_today_to_yesterday(self):
        """Test that today's date gets adjusted to yesterday"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        adjusted = adjust_end_date_for_data_quality(today)
        assert adjusted == yesterday
    
    def test_adjust_future_date_to_yesterday(self):
        """Test that future dates get adjusted to yesterday"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        future_date = today + timedelta(days=5)
        
        adjusted = adjust_end_date_for_data_quality(future_date)
        assert adjusted == yesterday
    
    def test_historical_date_unchanged(self):
        """Test that historical dates remain unchanged"""
        today = date.today()
        historical_date = today - timedelta(days=10)
        
        adjusted = adjust_end_date_for_data_quality(historical_date)
        assert adjusted == historical_date
    
    def test_yesterday_unchanged(self):
        """Test that yesterday's date remains unchanged"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        adjusted = adjust_end_date_for_data_quality(yesterday)
        assert adjusted == yesterday
    
    def test_edge_case_scenarios(self):
        """Test various edge case scenarios"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Test with dates far in the past
        old_date = date(2020, 1, 1)
        assert adjust_end_date_for_data_quality(old_date) == old_date
        
        # Test with dates far in the future
        future_date = date(2030, 12, 31)
        assert adjust_end_date_for_data_quality(future_date) == yesterday
        
        # Test with dates just before today
        two_days_ago = today - timedelta(days=2)
        assert adjust_end_date_for_data_quality(two_days_ago) == two_days_ago


if __name__ == "__main__":
    pytest.main([__file__])
