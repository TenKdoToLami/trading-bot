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
CACHE_FILE = os.path.join(DATA_DIR, "master_history.csv")


def load_spy_data(start_date: str = "1993-01-01", force_refresh: bool = False) -> pd.DataFrame:
    if not force_refresh and os.path.exists(CACHE_FILE):
        df = pd.read_csv(CACHE_FILE, index_col=0, parse_dates=True)
        if len(df) > 0 and 'vix' in df.columns:
            print(f"Loaded {len(df)} days from master cache ({CACHE_FILE})")
            return df

    import yfinance as yf

    print(f"Downloading master data (SPY, VIX, Yield Curve) since {start_date}...")
    
    # 1. SPY
    spy_raw = yf.download("SPY", start=start_date, progress=False)
    if isinstance(spy_raw.columns, pd.MultiIndex): spy_raw.columns = spy_raw.columns.get_level_values(0)
    
    # 2. VIX
    vix_raw = yf.download("^VIX", start=start_date, progress=False)
    if isinstance(vix_raw.columns, pd.MultiIndex): vix_raw.columns = vix_raw.columns.get_level_values(0)
    
    # 3. Yield Curve (FRED: T10Y2Y)
    try:
        fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=T10Y2Y"
        fred_data = pd.read_csv(fred_url, index_col="DATE", parse_dates=True, na_values=".")
        # Filter dates
        fred_data = fred_data[fred_data.index >= pd.to_datetime(start_date)]
    except Exception as e:
        print(f"Warning: Could not fetch FRED data: {e}. Filling with 0.")
        fred_data = pd.DataFrame(index=spy_raw.index)
        fred_data['T10Y2Y'] = 0.0

    # 4. Merge
    df = pd.DataFrame({
        "open": spy_raw["Open"],
        "high": spy_raw["High"],
        "low": spy_raw["Low"],
        "close": spy_raw["Close"],
        "volume": spy_raw["Volume"],
        "vix": vix_raw["Close"],
        "yield_curve": fred_data["T10Y2Y"]
    })
    
    # Fill missing macro data (Forward fill then zero for gaps)
    df['vix'] = df['vix'].ffill().fillna(15.0)
    df['yield_curve'] = df['yield_curve'].ffill().fillna(0.0)
    
    # Critical Fix: Drop days where SPY did not trade (like early Jan 1993)
    df = df.dropna(subset=['close'])
    
    df["spy_close"] = df["close"]
    df.index.name = "date"

    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(CACHE_FILE)
    print(f"Cached {len(df)} days to {CACHE_FILE}")

    return df
