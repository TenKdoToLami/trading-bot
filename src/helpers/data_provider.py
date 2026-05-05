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

def _compute_temporal_features(df):
    """Vectorized calculation of seasonality and turn-of-month flags."""
    import numpy as np
    
    # 1. Month Cycle (Seasonality)
    months = df.index.month
    angles = 2 * np.pi * (months - 1) / 12
    df['month_sin'] = np.sin(angles)
    df['month_cos'] = np.cos(angles)
    
    # 2. Turn-of-Month (Last trading day + First 3 trading days)
    # Binary mask: 1.0 if it's the last day of the month or one of the first three
    df['is_tom'] = 0.0
    
    # Group by month/year to find boundaries
    groups = df.groupby([df.index.year, df.index.month])
    
    for _, group in groups:
        # Last trading day
        df.loc[group.index[-1], 'is_tom'] = 1.0
        # First three trading days
        df.loc[group.index[:3], 'is_tom'] = 1.0
        
    return df


def load_spy_data(start_date: str = "1993-01-01", force_refresh: bool = False) -> pd.DataFrame:
    if not force_refresh and os.path.exists(CACHE_FILE):
        df = pd.read_csv(CACHE_FILE, index_col=0, parse_dates=True)
        # Check for V11 temporal columns
        if len(df) > 0 and 'vix' in df.columns and 'is_tom' in df.columns:
            print(f"Loaded {len(df)} days from master cache ({CACHE_FILE})")
            return df

    import yfinance as yf

    print(f"Downloading master data (SPY, VIX, Yield Curve, Credit Spread) since {start_date}...")
    
    # 1. SPY
    spy_raw = yf.download("SPY", start=start_date, progress=False)
    if isinstance(spy_raw.columns, pd.MultiIndex): spy_raw.columns = spy_raw.columns.get_level_values(0)
    
    # 2. VIX
    vix_raw = yf.download("^VIX", start=start_date, progress=False)
    if isinstance(vix_raw.columns, pd.MultiIndex): vix_raw.columns = vix_raw.columns.get_level_values(0)
    
    # 3. Yield Curve, Credit Spread, and Gold (FRED)
    def _fetch_fred(fred_id):
        try:
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={fred_id}"
            data = pd.read_csv(url, na_values=".")
            date_col = "DATE" if "DATE" in data.columns else "observation_date"
            if date_col in data.columns:
                data[date_col] = pd.to_datetime(data[date_col])
                data.set_index(date_col, inplace=True)
                return data[data.index >= pd.to_datetime(start_date)]
            return None
        except Exception as e:
            print(f"  Error fetching FRED {fred_id}: {e}")
            return None

    yc_data = _fetch_fred("T10Y2Y")
    cs_data = _fetch_fred("BAA10Y")

    # 4. Defensive Assets (VUSTX: Long Bonds, VFISX: Short Bonds, ^XAU: Gold/Silver Index)
    def_raw = yf.download(["VUSTX", "VFISX", "^XAU"], start=start_date, progress=False)
    if isinstance(def_raw.columns, pd.MultiIndex):
        def_close = def_raw["Close"]
    else:
        def_close = def_raw

    # 4. Merge
    df = pd.DataFrame({
        "open": spy_raw["Open"],
        "high": spy_raw["High"],
        "low": spy_raw["Low"],
        "close": spy_raw["Close"],
        "volume": spy_raw["Volume"],
        "vix": vix_raw["Close"] if vix_raw is not None else 15.0,
        "yield_curve": yc_data["T10Y2Y"] if yc_data is not None else 0.0,
        "credit_spread": cs_data["BAA10Y"] if cs_data is not None else 2.0,
        "gold": def_close["^XAU"] if "^XAU" in def_close.columns else 0.0,
        "tlt_proxy": def_close["VUSTX"] if "VUSTX" in def_close.columns else 0.0,
        "shy_proxy": def_close["VFISX"] if "VFISX" in def_close.columns else 0.0
    })

    # Fill missing macro data (Forward fill then defaults)
    df['vix'] = df['vix'].ffill().fillna(15.0)
    df['yield_curve'] = df['yield_curve'].ffill().fillna(0.0)
    df['credit_spread'] = df['credit_spread'].ffill().fillna(2.0)
    df['gold'] = df['gold'].ffill().bfill() # Gold fixing has gaps
    df['tlt_proxy'] = df['tlt_proxy'].ffill()
    df['shy_proxy'] = df['shy_proxy'].ffill()
    
    # Critical Fix: Drop days where SPY did not trade (like early Jan 1993)
    df = df.dropna(subset=['close'])
    
    df["spy_close"] = df["close"]
    df.index.name = "date"

    # Pre-calculate temporal features for V11+ speed
    df = _compute_temporal_features(df)

    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(CACHE_FILE)
    print(f"Cached {len(df)} days to {CACHE_FILE}")

    return df
