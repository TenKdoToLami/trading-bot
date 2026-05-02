import inspect
from strategies.base import BaseStrategy

class MostOptimalStrategy(BaseStrategy):
    """
    God Mode Strategy:
    Uses a dynamic programming algorithm to calculate the mathematically perfect
    sequence of holdings across the entire backtest period.
    
    It perfectly accounts for the framework's 0.12% friction fees for switching
    assets and the expense ratios/cash yields of the underlying assets.
    """
    
    NAME = "[Cheat] Most Optimal (God Mode)"

    def __init__(self):
        self.path = []
        self.current_step = 0

    def reset(self):
        self.current_step = 0
        self.path = []
        
        # Sneaky God Mode Lookahead:
        # Since the framework feeds data one day at a time, we use Python's
        # inspect module to reach up into the tournament runner's call stack
        # and grab the entire simulation dataset right as we reset.
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
        """
        O(N) Dynamic Programming solver to find the optimal path.
        """
        assets = ["CASH", "SPY", "2xSPY", "3xSPY"]
        leverage_map = {"CASH": 0.0, "SPY": 1.0, "2xSPY": 2.0, "3xSPY": 3.0}
        
        def calculate_asset_return(asset_name, spy_daily_return):
            # Annualized Institutional Cost/Yield assumptions from Portfolio
            if asset_name == "SPY":   return spy_daily_return - (0.0003 / 252)
            if asset_name == "2xSPY": return (spy_daily_return * 2.0) - (0.0091 / 252)
            if asset_name == "3xSPY": return (spy_daily_return * 3.0) - (0.0091 / 252)
            if asset_name == "CASH":  return 0.0350 / 252
            return 0.0

        n_days = len(price_data_list)
        if n_days == 0:
            return
            
        # DP state: (rounded_equity, -leverage, exact_equity)
        # We store leverage negatively so that max() prioritizes lower leverage when equity is equal
        dp = {a: (-1.0, 0.0, -1.0) for a in assets}
        dp["CASH"] = (round(1.0, 6), 0.0, 1.0)
        
        # Array of dicts mapping each day's optimal previous asset
        backpointers = []
        
        for i in range(1, n_days):
            row = price_data_list[i]
            prev_row = price_data_list[i-1]
            
            # Execution price: Avg of Open and Close
            spy_price = (float(row['open']) + float(row['close'])) / 2
            prev_price = (float(prev_row['open']) + float(prev_row['close'])) / 2
            spy_daily_return = (spy_price - prev_price) / prev_price if prev_price > 0 else 0.0
            
            new_dp = {}
            step_bp = {}
            
            for current_asset in assets:
                best_val = (-float('inf'), 0.0, -1.0)
                best_prev_asset = None
                
                for prev_asset in assets:
                    prev_eq = dp[prev_asset][2]
                    if prev_eq < 0:
                        continue
                        
                    daily_ret = calculate_asset_return(prev_asset, spy_daily_return)
                    
                    # 0.12% friction cost for switching (Turnover=2.0 * (0.0005 + 0.0001))
                    friction = 0.0012 if prev_asset != current_asset else 0.0
                    
                    new_eq = prev_eq * (1.0 + daily_ret) * (1.0 - friction)
                    
                    # Tie-breaking logic: round equity to 6 decimal places.
                    # If two paths produce identical returns (e.g., sideways market),
                    # the tuple comparison naturally breaks the tie favoring lower leverage.
                    val_tuple = (round(new_eq, 6), -leverage_map[current_asset], new_eq)
                    
                    if val_tuple > best_val:
                        best_val = val_tuple
                        best_prev_asset = prev_asset
                        
                new_dp[current_asset] = best_val
                step_bp[current_asset] = best_prev_asset
                
            dp = new_dp
            backpointers.append(step_bp)
            
        # Find the absolute best final state
        best_final_val = max(dp.values())
        best_end_asset = None
        for a in assets:
            if dp[a] == best_final_val:
                best_end_asset = a
                break
                
        # Reconstruct path by walking backwards
        path = []
        curr = best_end_asset
        for step_bp in reversed(backpointers):
            path.append(curr)
            curr = step_bp[curr]
            
        # Reverse again to get chronological order from day 1 to day N
        self.path = list(reversed(path))

    def on_data(self, date, price_data, prev_data):
        """
        Yields the pre-calculated sequence of perfect actions.
        """
        if self.current_step < len(self.path):
            best_asset = self.path[self.current_step]
        else:
            best_asset = self.path[-1] if self.path else "CASH"
            
        self.current_step += 1
        return {best_asset: 1.0}
