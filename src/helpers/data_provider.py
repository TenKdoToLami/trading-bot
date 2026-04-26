"""
Local-first SPY data provider.

Downloads historical SPY data from yfinance on first use,
then caches it to a local CSV for all subsequent runs.
"""

import os
import pandas as pd


# Paths relative to project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
CACHE_FILE = os.path.join(DATA_DIR, "spy_history.csv")


def load_spy_data(start_date: str = "1993-01-01", force_refresh: bool = False) -> pd.DataFrame:
    """
    Load SPY daily close prices with local-first caching.

    On first call (or if force_refresh=True), downloads from yfinance
    and saves to data/spy_history.csv.  Subsequent calls read from cache.

    Args:
        start_date:    Earliest date to fetch (ISO format).
        force_refresh: If True, re-download even if cache exists.

    Returns:
        DataFrame with DatetimeIndex named 'date' and column 'spy_close'.
    """
    if not force_refresh and os.path.exists(CACHE_FILE):
        df = pd.read_csv(CACHE_FILE, index_col=0, parse_dates=True)
        if len(df) > 0:
            print(f"Loaded {len(df)} days from local cache ({CACHE_FILE})")
            return df

    # Download fresh data
    import yfinance as yf

    print(f"Downloading SPY data from yfinance (since {start_date})...")
    spy_df = yf.download("SPY", start=start_date, progress=False)

    if isinstance(spy_df.columns, pd.MultiIndex):
        spy_df.columns = spy_df.columns.get_level_values(0)

    df = pd.DataFrame({"spy_close": spy_df["Close"]})
    df.index.name = "date"

    # Cache locally
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(CACHE_FILE)
    print(f"Cached {len(df)} days to {CACHE_FILE}")

    return df
