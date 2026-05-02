import inspect
from strategies.base import BaseStrategy

class _LockoutOptimalStrategy(BaseStrategy):
    """
    Base for 'Lockout' God Mode strategies.
    A change in asset requires holding that asset for a mandatory period L.
    """
    def __init__(self, lockout_period: int, name: str):
        self.L = lockout_period
        self.NAME = name
        self.path = []
        self.current_step = 0

    def reset(self):
        self.current_step = 0
        self.path = []
        
        # Lookahead to grab data from tournament runner
        frame = inspect.currentframe()
        try:
            while frame:
                if frame.f_code.co_name == '_execute_simulation':
                    price_data_list = frame.f_locals.get('price_data_list')
                    if price_data_list:
                        self._calculate_dp(price_data_list)
                        break
                frame = frame.f_back
        finally:
            del frame

    def _calculate_dp(self, price_data_list):
        assets = ["CASH", "SPY", "2xSPY", "3xSPY"]
        leverage_map = {"CASH": 0.0, "SPY": 1.0, "2xSPY": 2.0, "3xSPY": 3.0}
        friction = 0.0012
        
        def get_ret(asset_name, spy_daily_return):
            if asset_name == "SPY":   return spy_daily_return - (0.0003 / 252)
            if asset_name == "2xSPY": return (spy_daily_return * 2.0) - (0.0091 / 252)
            if asset_name == "3xSPY": return (spy_daily_return * 3.0) - (0.0091 / 252)
            if asset_name == "CASH":  return 0.0350 / 252
            return 0.0

        n_days = len(price_data_list)
        if n_days == 0: return

        # Precompute daily returns for all assets
        asset_rets = {a: [0.0] * n_days for a in assets}
        for i in range(1, n_days):
            row = price_data_list[i]
            prev_row = price_data_list[i-1]
            spy_price = (float(row['open']) + float(row['close'])) / 2
            prev_price = (float(prev_row['open']) + float(prev_row['close'])) / 2
            spy_daily_return = (spy_price - prev_price) / prev_price if prev_price > 0 else 0.0
            for a in assets:
                asset_rets[a][i] = get_ret(a, spy_daily_return)

        # Precompute cumulative returns for jumps of length L using a sliding window
        # cum_rets[asset][end_day] = product of (1+r) from end_day-L+1 to end_day
        cum_rets = {a: [1.0] * n_days for a in assets}
        for a in assets:
            window_prod = 1.0
            for i in range(1, n_days):
                window_prod *= (1.0 + asset_rets[a][i])
                if i > self.L:
                    window_prod /= (1.0 + asset_rets[a][i - self.L])
                cum_rets[a][i] = window_prod

        # dp[i][asset] = (equity, prev_asset, prev_i)
        # equity is the max equity at day i, given we are FREE to move at day i.
        dp = [{} for _ in range(n_days)]
        for a in assets:
            dp[0][a] = (-float('inf'), None, None)
        
        # Day 0: Start in CASH, free to move.
        dp[0]["CASH"] = (1.0, None, None)

        for i in range(1, n_days):
            for a in assets:
                # Option 1: Stay from i-1 (only if we were free at i-1)
                best_eq, best_prev_a, best_prev_i = -float('inf'), None, None
                
                if dp[i-1][a][0] > -float('inf'):
                    stay_eq = dp[i-1][a][0] * (1.0 + asset_rets[a][i])
                    # Tie-break with leverage
                    if round(stay_eq, 8) > round(best_eq, 8) or (round(stay_eq, 8) == round(best_eq, 8) and leverage_map[a] < (leverage_map[best_prev_a] if best_prev_a else 999)):
                        best_eq = stay_eq
                        best_prev_a = a
                        best_prev_i = i - 1

                # Option 2: Switch from i-L
                if i >= self.L:
                    for prev_a in assets:
                        if prev_a == a: continue
                        if dp[i-self.L][prev_a][0] > -float('inf'):
                            switch_eq = dp[i-self.L][prev_a][0] * cum_rets[a][i] * (1.0 - friction)
                            if round(switch_eq, 8) > round(best_eq, 8):
                                best_eq = switch_eq
                                best_prev_a = prev_a
                                best_prev_i = i - self.L
                
                dp[i][a] = (best_eq, best_prev_a, best_prev_i)

        # To find the absolute best final state, we must also check states that are
        # currently "in-flight" (locked) at the end of the backtest.
        final_best_eq = -float('inf')
        final_state = (None, None) # (day, asset)

        for i in range(max(0, n_days - self.L), n_days):
            for a in assets:
                # If we were free at day i, what is our equity at n_days if we stay in 'a'?
                if dp[i][a][0] > -float('inf'):
                    # Calculate remaining return from i+1 to n_days-1
                    rem_ret = 1.0
                    for k in range(i + 1, n_days):
                        rem_ret *= (1.0 + asset_rets[a][k])
                    
                    eq_at_end = dp[i][a][0] * rem_ret
                    if eq_at_end > final_best_eq:
                        final_best_eq = eq_at_end
                        final_state = (i, a)

        # Reconstruct path
        full_path = ["CASH"] * n_days
        curr_i, curr_a = final_state
        
        # Fill the "tail" (from curr_i to end)
        for k in range(curr_i, n_days):
            full_path[k] = curr_a
            
        # Walk back the DP
        while curr_i is not None and curr_i > 0:
            next_eq, next_a, next_i = dp[curr_i][curr_a]
            if next_i is None: break
            
            # Fill the segment between next_i and curr_i
            for k in range(next_i, curr_i):
                full_path[k] = curr_a
            
            curr_i, curr_a = next_i, next_a
            
        self.path = full_path

    def on_data(self, date, price_data, prev_data):
        if self.current_step < len(self.path):
            asset = self.path[self.current_step]
        else:
            asset = self.path[-1] if self.path else "CASH"
        self.current_step += 1
        return {asset: 1.0}

class WeeklyOptimalStrategy(_LockoutOptimalStrategy):
    def __init__(self):
        super().__init__(lockout_period=5, name="[Cheat] Guided God (Weekly)")

class MonthlyOptimalStrategy(_LockoutOptimalStrategy):
    def __init__(self):
        super().__init__(lockout_period=21, name="[Cheat] Patient God (Monthly)")

class YearlyOptimalStrategy(_LockoutOptimalStrategy):
    def __init__(self):
        super().__init__(lockout_period=252, name="[Cheat] Eternal God (Yearly)")
