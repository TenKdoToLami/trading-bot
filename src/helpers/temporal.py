import numpy as np
import pandas as pd

def get_month_cycle(date):
    """
    Returns (sin, cos) of the month to capture seasonality smoothly.
    1.0 = January, 12.0 = December.
    """
    month = date.month
    angle = 2 * np.pi * (month - 1) / 12
    return np.sin(angle), np.cos(angle)

def is_turn_of_month(date, prices_df=None):
    """
    Returns 1.0 if the date is within the 'Turn of the Month' window:
    - Last 1 trading day of the current month
    - First 3 trading days of the next month
    
    If prices_df is provided, it uses actual trading days.
    Otherwise, it approximates based on calendar days (less accurate).
    """
    if prices_df is not None and not prices_df.empty:
        # Get all dates in the same month as 'date'
        month_dates = prices_df.index[prices_df.index.month == date.month]
        if len(month_dates) == 0:
            return 0.0
            
        month_dates = sorted(month_dates)
        
        # Is it the last trading day of the month?
        if date == month_dates[-1]:
            return 1.0
            
        # Is it one of the first 3 trading days of the month?
        if date in month_dates[:3]:
            return 1.0
            
    return 0.0

def get_day_of_week(date):
    """Normalized day of week (0-4 for Mon-Fri)."""
    return float(date.dayofweek) / 4.0

def get_days_to_opex(date):
    """
    Distance to monthly Options Expiration (3rd Friday).
    Normalized to ~0.0-1.0 (approx 20 trading days).
    """
    # Simplified approximation: 3rd Friday of the month
    # First day of month
    first_day = date.replace(day=1)
    # Day of week of first day (0=Mon, 4=Fri)
    w = first_day.weekday()
    # Days to first Friday
    to_first_fri = (4 - w) % 7
    # 3rd Friday
    opex_day = first_day.replace(day=1 + to_first_fri + 14)
    
    delta = (opex_day - date).days
    if delta < 0:
        # Already passed, look at next month's opex
        # (Simplified: just return 1.0)
        return 1.0
        
    return min(1.0, delta / 21.0)
