import os
import json
import argparse
import pandas as pd
import numpy as np
from tqdm import tqdm
from src.helpers.indicators import (
    sma, ema, rsi, macd, adx, atr, realized_volatility, linear_regression_slope, mfi, trix
)

class V10Profiler:
    """
    Model V10 Indicator Sensitivity Profiler.
    Scans historical data to find the optimal 'lookback' and 'certainty threshold' 
    for every indicator to maximize predictive power for bullish and bearish regimes.
    """
    
    def __init__(self, data_path, horizon=20, min_precision=0.65):
        self.df = pd.read_csv(data_path)
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df = self.df.sort_values('date')
        self.horizon = horizon
        self.min_precision = min_precision
        
        # Labels: Forward returns over the horizon
        self.df['fwd_ret'] = self.df['close'].shift(-horizon) / self.df['close'] - 1.0
        
        # Targets for classification
        # We look for "Certainty" - a significant move in the target direction
        self.df['is_bullish'] = (self.df['fwd_ret'] > 0.03).astype(int) 
        self.df['is_bearish'] = (self.df['fwd_ret'] < -0.03).astype(int)
        
        self.prices = self.df['close'].tolist()
        self.highs = self.df['high'].tolist()
        self.lows = self.df['low'].tolist()
        self.volumes = self.df.get('volume', pd.Series([0]*len(self.df))).tolist()
        
    def _find_best_rule(self, values, target_col):
        """Helper to find best threshold and condition for a set of calculated values."""
        results = []
        self.df['val'] = values
        
        v_min, v_max = self.df['val'].min(), self.df['val'].max()
        steps = np.linspace(v_min, v_max, 20)
        
        for condition in ['greater', 'less']:
            for thresh in steps:
                if condition == 'greater':
                    subset = self.df[self.df['val'] > thresh]
                else:
                    subset = self.df[self.df['val'] < thresh]
                    
                if len(subset) > 50:
                    precision = subset[target_col].mean()
                    results.append({
                        'thresh': float(thresh), 
                        'precision': float(precision), 
                        'freq': len(subset)/len(self.df),
                        'condition': condition
                    })
        
        if not results: return None
        res_df = pd.DataFrame(results)
        
        baseline = self.df[target_col].mean()
        # Only keep results where precision is meaningfully better than baseline
        res_df = res_df[res_df['precision'] > baseline * 1.1]
        if res_df.empty: return None
        
        # Maximize excess precision (edge) while maintaining some frequency
        res_df['score'] = (res_df['precision'] - baseline) * np.sqrt(res_df['freq'])
        return res_df.loc[res_df['score'].idxmax()].to_dict()

    def profile_moving_averages(self, mode='SMA'):
        print(f"Profiling {mode} Distance...")
        bull_results = []
        bear_results = []
        for lb in tqdm(range(10, 301, 20)):
            values = []
            prev = None
            for i in range(len(self.prices)):
                if mode == 'SMA':
                    ma = sma(self.prices[:i+1], lb)
                else:
                    ma = ema(self.prices[:i+1], lb, prev_ema=prev)
                    prev = ma
                dist = (self.prices[i] - ma) / ma if ma else 0
                values.append(dist)
            
            best_bull = self._find_best_rule(values, 'is_bullish')
            if best_bull: bull_results.append({**best_bull, 'lookback': lb})
            
            best_bear = self._find_best_rule(values, 'is_bearish')
            if best_bear: bear_results.append({**best_bear, 'lookback': lb})
            
        return self._extract_best(bull_results, bear_results, f"{mode}_DIST")

    def profile_oscillators(self, mode='RSI'):
        print(f"Profiling {mode}...")
        bull_results = []
        bear_results = []
        for lb in tqdm(range(5, 61, 5)):
            values = []
            state = {}
            for i in range(len(self.prices)):
                if mode == 'RSI':
                    val = rsi(self.prices[:i+1], lb, state=state)
                elif mode == 'MFI':
                    val = mfi(self.highs[:i+1], self.lows[:i+1], self.prices[:i+1], self.volumes[:i+1], lb)
                elif mode == 'TRIX':
                    val = trix(self.prices[:i+1], lb, state=state)
                values.append(val if val is not None else 50 if mode != 'TRIX' else 0)
            
            b_bull = self._find_best_rule(values, 'is_bullish')
            b_bear = self._find_best_rule(values, 'is_bearish')
            
            if b_bull: bull_results.append({**b_bull, 'lookback': lb})
            if b_bear: bear_results.append({**b_bear, 'lookback': lb})
            
        return self._extract_best(bull_results, bear_results, mode)

    def profile_trend(self):
        print("Profiling ADX & Slope...")
        # ADX
        adx_bull = []
        adx_bear = []
        for lb in tqdm(range(7, 31, 7), desc="ADX"):
            values = []
            state = {}
            for i in range(len(self.prices)):
                val = adx(self.highs[:i+1], self.lows[:i+1], self.prices[:i+1], lb, state=state)
                values.append(val if val is not None else 20)
            b_bull = self._find_best_rule(values, 'is_bullish')
            if b_bull: adx_bull.append({**b_bull, 'lookback': lb})
        
        # Slope
        slope_bull = []
        slope_bear = []
        for lb in tqdm(range(10, 101, 10), desc="Slope"):
            values = []
            for i in range(len(self.prices)):
                val = linear_regression_slope(self.prices[:i+1], lb)
                values.append(val / self.prices[i] * 1000 if val and self.prices[i] else 0)
            b_bull = self._find_best_rule(values, 'is_bullish')
            b_bear = self._find_best_rule(values, 'is_bearish')
            if b_bull: slope_bull.append({**b_bull, 'lookback': lb})
            if b_bear: slope_bear.append({**b_bear, 'lookback': lb})
            
        return {
            "ADX": self._extract_best(adx_bull, [], "ADX"),
            "SLOPE": self._extract_best(slope_bull, slope_bear, "SLOPE")
        }

    def _extract_best(self, bull_list, bear_list, name):
        best_bull = None
        if bull_list:
            bull_df = pd.DataFrame(bull_list)
            best_bull = bull_df.loc[bull_df['score'].idxmax()].to_dict()
            
        best_bear = None
        if bear_list:
            bear_df = pd.DataFrame(bear_list)
            best_bear = bear_df.loc[bear_df['score'].idxmax()].to_dict()
            
        return {
            "name": name,
            "bullish": best_bull,
            "bearish": best_bear
        }

    def run(self, output_path):
        profiles = {}
        profiles['SMA_DIST'] = self.profile_moving_averages('SMA')
        profiles['EMA_DIST'] = self.profile_moving_averages('EMA')
        profiles['RSI'] = self.profile_oscillators('RSI')
        profiles['MFI'] = self.profile_oscillators('MFI')
        profiles['TRIX'] = self.profile_oscillators('TRIX')
        
        trend_data = self.profile_trend()
        profiles['ADX'] = trend_data['ADX']
        profiles['SLOPE'] = trend_data['SLOPE']
        
        # Add basic Volatility check
        print("Profiling Volatility...")
        vol_bear = []
        for lb in tqdm(range(10, 61, 10)):
            values = [realized_volatility(self.prices[:i+1], lb) or 0.15 for i in range(len(self.prices))]
            res = self._find_best_rule(values, 'is_bearish')
            if res: vol_bear.append({**res, 'lookback': lb})
        profiles['VOL'] = self._extract_best([], vol_bear, "VOL")
        
        # Metadata
        meta = {
            "horizon": self.horizon,
            "generated_at": pd.Timestamp.now().isoformat(),
            "profiles": profiles
        }
        
        with open(output_path, 'w') as f:
            json.dump(meta, f, indent=4)
        print(f"Profiling complete. Results saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/SPY.csv")
    parser.add_argument("--out", default="champions/v10_alpha/indicator_profiles.json")
    parser.add_argument("--horizon", type=int, default=20)
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    profiler = V10Profiler(args.data, horizon=args.horizon)
    profiler.run(args.out)
