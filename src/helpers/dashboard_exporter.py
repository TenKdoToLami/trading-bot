import json
import os
import numpy as np

def export_to_dashboard(report_data, output_path="visualizer/public/data.json"):
    """
    Exports tournament results to a JSON file for the dashboard.
    """
    # Ensure project root is correct
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    full_output_path = os.path.join(project_root, output_path)
    
    os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
    
    # Subsample equity curves and drawdowns for frontend performance
    for strategy in report_data:
        if 'curve' in strategy:
            strategy['curve']['dates'] = strategy['curve']['dates'][::5]
            strategy['curve']['equities'] = strategy['curve']['equities'][::5]
            
            # Subsample drawdowns if available in metrics
            if 'drawdowns' in strategy.get('metrics', {}):
                strategy['metrics']['drawdowns'] = strategy['metrics']['drawdowns'][::5]
                
            # Subsample leverage and regime history
            if 'history' in strategy:
                strategy['history']['leverage'] = strategy['history']['leverage'][::5]
                strategy['history']['regime'] = strategy['history']['regime'][::5]
                
        # Calculate Yearly Returns for the bar chart
        if 'curve' in strategy:
            dates = strategy['curve']['dates']
            equities = strategy['curve']['equities']
            yearly = {}
            for d, e in zip(dates, equities):
                year = d[:4]
                if year not in yearly:
                    yearly[year] = [e]
                else:
                    yearly[year].append(e)
            
            yearly_returns = []
            years = sorted(yearly.keys())
            for i in range(len(years)):
                y = years[i]
                start_val = yearly[y][0]
                end_val = yearly[y][-1]
                # For more accuracy, use the end of the previous year
                if i > 0:
                    start_val = yearly[years[i-1]][-1]
                
                ret = (end_val / start_val) - 1
                yearly_returns.append({"year": y, "return": round(ret * 100, 2)})
            strategy['metrics']['yearly_returns'] = yearly_returns
            
            # Calculate rolling 1yr volatility (252 days)
            daily_rets = np.diff(equities) / equities[:-1]
            rolling_vol = []
            window = 252 // 5 # Subsampled window
            for i in range(len(daily_rets)):
                if i < window:
                    rolling_vol.append(None)
                else:
                    vol = np.std(daily_rets[i-window:i]) * np.sqrt(252 / 5)
                    rolling_vol.append(round(float(vol) * 100, 2))
            strategy['metrics']['rolling_vol'] = rolling_vol

    with open(full_output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f)
        
    print(f"[DASHBOARD] Results exported to {output_path}")
