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
                
            # Subsample telemetry history (Confidences, etc)
            if 'telemetry' in strategy:
                for key in strategy['telemetry']:
                    strategy['telemetry'][key] = strategy['telemetry'][key][::5]
                
        # Calculate Yearly & Monthly Returns
        if 'curve' in strategy:
            dates = strategy['curve']['dates']
            equities = strategy['curve']['equities']
            
            # Monthly grouping
            monthly_data = {}
            for d, e in zip(dates, equities):
                month_key = d[:7] # YYYY-MM
                if month_key not in monthly_data:
                    monthly_data[month_key] = [e]
                else:
                    monthly_data[month_key].append(e)
            
            # Monthly Returns
            monthly_returns = []
            m_keys = sorted(monthly_data.keys())
            for i in range(len(m_keys)):
                key = m_keys[i]
                start_val = monthly_data[key][0]
                end_val = monthly_data[key][-1]
                if i > 0:
                    start_val = monthly_data[m_keys[i-1]][-1]
                ret = (end_val / start_val) - 1
                monthly_returns.append({"month": key, "return": round(ret * 100, 2)})
            strategy['metrics']['monthly_returns'] = monthly_returns

            # Yearly Aggregation from monthly
            yearly = {}
            for m in monthly_returns:
                y = m['month'][:4]
                if y not in yearly: yearly[y] = []
                yearly[y].append(m['return'])
            
            strategy['metrics']['yearly_returns'] = [
                {"year": y, "return": round(sum(rets), 2)} for y, rets in sorted(yearly.items())
            ]

            # Monthly Confidence Aggregation
            if 'telemetry' in strategy and 'conf_3x' in strategy['telemetry']:
                tel = strategy['telemetry']
                conf_monthly = {}
                for i, d in enumerate(dates):
                    month_key = d[:7]
                    if month_key not in conf_monthly:
                        conf_monthly[month_key] = {"3x": [], "2x": [], "1x": [], "Cash": []}
                    conf_monthly[month_key]["3x"].append(tel['conf_3x'][i])
                    conf_monthly[month_key]["2x"].append(tel['conf_2x'][i])
                    conf_monthly[month_key]["1x"].append(tel['conf_1x'][i])
                    conf_monthly[month_key]["Cash"].append(tel['conf_cash'][i])
                
                strategy['telemetry']['monthly_avg'] = [
                    {
                        "month": k,
                        "conf_3x": float(np.nan_to_num(np.mean(v["3x"]))) if v["3x"] else 0.0,
                        "conf_2x": float(np.nan_to_num(np.mean(v["2x"]))) if v["2x"] else 0.0,
                        "conf_1x": float(np.nan_to_num(np.mean(v["1x"]))) if v["1x"] else 0.0,
                        "conf_cash": float(np.nan_to_num(np.mean(v["Cash"]))) if v["Cash"] else 0.0
                    } for k, v in sorted(conf_monthly.items())
                ]

                # Signal Trace for Neural strategies (subsampled 5-day)
                if 'score_panic' in tel:
                    trace = []
                    step = 5
                    for i in range(0, len(dates), step):
                        point = {
                            "date": dates[i],
                            "p_score": float(tel['score_panic'][i]),
                            "p_thresh": float(tel.get('threshold_panic', [0]*len(dates))[i]),
                            "b_score": float(tel.get('score_bull', tel.get('score_3x', [0]*len(dates)))[i]),
                            "b_thresh": float(tel.get('threshold_bull', tel.get('threshold_3x', [0]*len(dates)))[i]),
                        }
                        # Add V2 Multi-Brain Specifics
                        if 'score_2x' in tel:
                            point["s2_score"] = float(tel['score_2x'][i])
                            point["s2_thresh"] = float(tel.get('threshold_2x', [0]*len(dates))[i])
                        if 'score_1x' in tel:
                            point["s1_score"] = float(tel['score_1x'][i])
                            point["s1_thresh"] = float(tel.get('threshold_1x', [0]*len(dates))[i])
                            
                        trace.append(point)
                    strategy['telemetry']['signal_trace'] = trace

            # Special Case: V1/V2 Regime Matrix (Bucket-based)
            genome = strategy.get('genome')
            if genome and "bounds_p" in genome and "weights_p" in genome:
                bounds = genome["bounds_p"]
                weights = genome["weights_p"]
                matrix = []
                for i in range(len(weights)):
                    if i == 0:
                        label = f"VIX < {bounds[0]}"
                    elif i < len(bounds):
                        label = f"{bounds[i-1]} - {bounds[i]}"
                    else:
                        label = f"VIX > {bounds[-1]}"
                        
                    w = weights[i]
                    matrix.append({
                        "label": label,
                        "cash": w[0],
                        "spy": w[1],
                        "triple": w[2]
                    })
                if 'telemetry' not in strategy:
                    strategy['telemetry'] = {}
                strategy['telemetry']['regime_matrix'] = matrix

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
