"""
Tournament runner — the central control unit.

Loads SPY data, discovers strategy plugins, feeds each strategy
one day at a time, and collects results for comparison.
"""

import hashlib
import concurrent.futures
from src.helpers.report_template import REPORT_TEMPLATE
import json
import importlib
import os
import random
import sys
import time
import numpy as np

from src.helpers.data_provider import load_spy_data
from src.tournament.portfolio import Portfolio
from strategies.base import BaseStrategy

def _execute_simulation(strategy_type, price_data_list, dates, strategy_kwargs=None):
    """Standalone simulation function for parallel execution."""
    kwargs = strategy_kwargs or {}
    strategy = strategy_type(**kwargs)
    strategy.reset()
    
    portfolio = Portfolio()
    pending_holdings = None
    
    for i in range(len(price_data_list)):
        date_str = str(dates[i].date()) if hasattr(dates[i], 'date') else str(dates[i])
        row = price_data_list[i]
        
        # Execution price: Avg of Open and Close
        spy_price = (float(row['open']) + float(row['close'])) / 2
        prev_row = price_data_list[i-1] if i > 0 else None

        # 1. Apply today's return using CURRENT holdings
        if i > 0:
            prev_price = (float(prev_row['open']) + float(prev_row['close'])) / 2
            daily_ret = (spy_price - prev_price) / prev_price
            portfolio.apply_daily_return(date_str, daily_ret)
            if portfolio.is_liquidated:
                break

        # 2. Execute yesterday's signal
        if pending_holdings is not None:
            portfolio.rebalance(date_str, pending_holdings)
            pending_holdings = None

        # 3. Generate signal for tomorrow
        result = strategy.on_data(date_str, row, prev_row)
        if result is not None:
            pending_holdings = result
            
    return {
        "metrics": portfolio.get_metrics(),
        "portfolio": portfolio
    }

def _generate_synthetic_series(df, chunk_size=252):
    """Creates a synthetic series via Block Bootstrapping."""
    total_len = len(df)
    indices = []
    while len(indices) < total_len:
        start = random.randint(0, total_len - chunk_size)
        indices.extend(range(start, start + chunk_size))
    indices = indices[:total_len]
    
    synthetic = df.iloc[indices].copy()
    returns = synthetic['close'].pct_change().fillna(0)
    
    new_close = [df['close'].iloc[0]]
    for r in returns[1:]:
        new_close.append(new_close[-1] * (1 + r))
    synthetic['close'] = new_close
    return synthetic

def _run_audit_batch(strategy_type, full_records, full_dates, strategy_kwargs, iterations=50, mode='resilience'):
    """Runs a batch of simulations for resilience or synthetic audits."""
    results = []
    total_len = len(full_records)
    
    # Pre-calculate returns (if missing)
    for i in range(len(full_records)):
        if 'ret' not in full_records[i]:
            if i == 0: full_records[i]['ret'] = 0
            else:
                p0 = full_records[i-1]['close']
                full_records[i]['ret'] = (full_records[i]['close'] - p0) / p0 if p0 != 0 else 0

    for i in range(iterations):
        if mode == 'resilience':
            window = 252 * 10
            start = random.randint(0, total_len - window)
            price_list = full_records[start : start + window]
            dates = full_dates[start : start + window]
        else:
            # Synthetic uses DETERMINISTIC SEEDING (same for all strategies)
            random.seed(42 + i) 
            
            chunk_size = 252
            shuffled_records = []
            while len(shuffled_records) < total_len:
                start = random.randint(0, total_len - chunk_size)
                shuffled_records.extend(full_records[start : start + chunk_size])
            shuffled_records = shuffled_records[:total_len]
            
            # Reconstruct price series
            price_list = []
            current_price = full_records[0]['close']
            for rec in shuffled_records:
                current_price *= (1 + rec['ret'])
                new_rec = rec.copy()
                new_rec['close'] = current_price
                scale = current_price / rec['close'] if rec['close'] != 0 else 1
                new_rec['open'] *= scale
                new_rec['high'] *= scale
                new_rec['low'] *= scale
                price_list.append(new_rec)
            
            dates = full_dates[:total_len]
            
        res = _execute_simulation(strategy_type, price_list, dates, strategy_kwargs)
        results.append(res['metrics'])
    
    random.seed(None)
    return {
        "avg_cagr": float(np.mean([m['cagr'] * 100 for m in results])),
        "med_cagr": float(np.median([m['cagr'] * 100 for m in results])),
        "avg_dd": float(np.mean([m['max_dd'] * 100 for m in results])),
        "med_dd": float(np.median([m['max_dd'] * 100 for m in results])),
        "avg_sharpe": float(np.mean([m['sharpe'] for m in results])),
        "avg_trades": float(np.mean([m['trades_per_year'] for m in results]))
    }

class TournamentRunner:
    def __init__(self, start_date="1993-01-01", end_date=None):
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.results = {}

    def load_data(self, force_refresh=False):
        print(f"Loading market data from {self.start_date}...")
        self.data = load_spy_data(self.start_date, force_refresh=force_refresh)
        if self.end_date:
            self.data = self.data[:self.end_date]
        return self.data

    def _clean_name(self, name, category, genome=None):
        """Standardizes and shortens strategy names."""
        n = name.replace("Buy & Hold", "B&H")
        n = n.replace("VOO", "SPY")
        n = n.replace("S&P 500", "SPY")
        n = n.replace("Simple Moving Average", "SMA")
        n = n.replace("Exponential Moving Average", "EMA")
        n = n.replace("Golden Cross", "GC")
        n = n.replace("Realized Volatility", "RealVol")
        n = n.replace("Manual Configuration", "Manual")
        n = n.replace("Precision Binary", "Precision")
        n = n.replace("Multi-Brain", "Multi")
        n = n.replace("Recovery:", "Rec:")
        n = n.replace("Price Confirm", "PC")
        n = n.replace("Vol Crush", "VC")
        n = n.replace("Exit ", "")
        n = n.replace("Champion ", "")
        n = n.replace("Genome ", "")
        n = n.replace("Strategy", "")
        
        # Remove extra underscores and fix spacing
        n = n.replace("_", " ").strip()
        
        if category == "CHAMP":
            return f"[CHAMP] {n}"
        if category == "BASE":
            return f"[BASE] {n}"
        if genome:
            g_str = json.dumps(genome, sort_keys=True)
            g_hash = hashlib.md5(g_str.encode()).hexdigest()[:4]
            return f"[GENE] {n} ({g_hash})"
        return n

    def discover_strategies(self):
        strategies = []
        # 1. Search strategies/ folder
        strat_dir = os.path.join(os.path.dirname(__file__), "..", "..", "strategies")
        if os.path.exists(strat_dir):
            for f in os.listdir(strat_dir):
                if f.endswith(".py") and f != "base.py":
                    module_name = f"strategies.{f[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        for attr in dir(module):
                            cls = getattr(module, attr)
                            if (isinstance(cls, type) and 
                                issubclass(cls, BaseStrategy) and 
                                cls != BaseStrategy and 
                                not attr.startswith("_") and
                                cls.__module__ == module_name):
                                
                                s = cls()
                                if not getattr(s, "NAME", None): s.NAME = attr
                                
                                # Skip evolution templates (raw Genome classes in strategies folder)
                                if "Genome" in attr or "[GENE]" in str(getattr(s, "NAME", "")):
                                    continue
                                    
                                cat = "BASE" if "B&H" in s.NAME or "Buy & Hold" in s.NAME else "IND"
                                s.NAME = self._clean_name(s.NAME, cat)
                                strategies.append(s)
                    except Exception as e:
                        print(f"  Error loading strategy {module_name}: {e}")

        # 2. Search champions/ folder for JSON genomes and Bridges
        champ_dir = os.path.join(os.path.dirname(__file__), "..", "..", "champions")
        if os.path.exists(champ_dir):
            for root, dirs, files in os.walk(champ_dir):
                # Skip vault directories to avoid loading historical noise
                if 'vault' in root.lower():
                    continue
                
                # A. Look for JSON genomes (Dynamic Champions) - ONLY genome.json
                for f in files:
                    if f.lower() == "genome.json":
                        json_path = os.path.join(root, f)
                        try:
                            with open(json_path, "r") as jf:
                                genome = json.load(jf)
                            
                            version = genome.get('version', 0.0)
                            if version == 0.0:
                                # Detection for legacy V1 structures
                                if "bounds_p" in genome or "weights_p" in genome:
                                    version = 1.0
                                elif "panic_weights" in genome:
                                    # V1 Classic (GenomeStrategy)
                                    version = 1.1 
                                else:
                                    folder_name = os.path.basename(root).lower()
                                    if "v6" in folder_name: version = 6.0
                                    elif "v5" in folder_name: version = 5.0
                                    elif "v4" in folder_name: version = 4.0
                                    elif "v3" in folder_name: version = 3.0
                                    elif "v2" in folder_name: version = 2.0
                                
                            strat_cls = None
                            
                            if version == 6.0:
                                from strategies.genome_v6_balancer import GenomeV6
                                strat_cls = GenomeV6
                            elif version == 5.0:
                                from strategies.genome_v5_sniper import GenomeV5Sniper
                                strat_cls = GenomeV5Sniper
                            elif version == 4.0:
                                folder_name = os.path.basename(root).lower()
                                if "chameleon" in folder_name:
                                    from strategies.genome_v4_chameleon import ChameleonV4
                                    strat_cls = ChameleonV4
                                else:
                                    from strategies.genome_v4_precision import GenomeV4Precision
                                    strat_cls = GenomeV4Precision
                            elif version == 3.0:
                                from strategies.genome_v3_precision import GenomeV3Strategy
                                strat_cls = GenomeV3Strategy
                            elif version == 2.0:
                                from strategies.genome_v2_multi import GenomeV2Strategy
                                strat_cls = GenomeV2Strategy
                            elif version == 1.1:
                                from strategies._genome_strategy import GenomeStrategy
                                strat_cls = GenomeStrategy
                            elif version == 1.0:
                                from strategies.genome_v1_manual import ManualV1
                                strat_cls = ManualV1
                                
                            if strat_cls:
                                s = strat_cls(genome=genome)
                                
                                # Professional Naming: Champion VX (Name)
                                folder_name = os.path.basename(root)
                                if f.lower() == "genome.json":
                                    # Convert v6_balancer -> Champion V6 (Balancer)
                                    parts = folder_name.split("_")
                                    ver = parts[0].upper() # V6
                                    name = " ".join(p.capitalize() for p in parts[1:]) # Balancer
                                    s.NAME = f"Champion {ver} ({name})"
                                else:
                                    # Fallback for other JSONs
                                    label = f.replace(".json", "")
                                    s.NAME = self._clean_name(label, "GENE", genome)
                                    
                                strategies.append(s)
                        except Exception as e:
                            print(f"  Error loading genome {f}: {e}")

                # B. Look for manual strategy.py Bridges (Legacy/Manual Champions)
                if "strategy.py" in files:
                    # (Keep existing bridge logic for non-json strategies)
                    rel_path = os.path.relpath(root, os.path.join(os.path.dirname(__file__), "..", ".."))
                    module_name = rel_path.replace(os.sep, ".") + ".strategy"
                    try:
                        module = importlib.import_module(module_name)
                        for attr in dir(module):
                            cls = getattr(module, attr)
                            if (isinstance(cls, type) and issubclass(cls, BaseStrategy) and cls != BaseStrategy and not attr.startswith("_")):
                                s = cls()
                                if not any(existing.NAME == s.NAME for existing in strategies):
                                    strategies.append(s)
                    except Exception as e:
                        print(f"  Error loading champion {module_name}: {e}")
        return strategies

    def run_all(self):
        if self.data is None: self.load_data()
        strategies = self.discover_strategies()
        return self._run_set(strategies)

    def run_single(self, strategy_name: str):
        if self.data is None: self.load_data()
        all_strats = self.discover_strategies()
        match = next((s for s in all_strats if s.NAME.lower() == strategy_name.lower()), None)
        if not match:
            raise ValueError(f"Strategy {strategy_name} not found.")
        return self._run_set([match])

    def _run_set(self, strategies):
        print(f"\nRunning simulation for {len(strategies)} strategies...")
        cols = ['open', 'high', 'low', 'close', 'volume', 'vix', 'yield_curve']
        price_list = self.data[cols].to_dict('records')
        dates = self.data.index

        results = {}
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_to_name = {
                executor.submit(_execute_simulation, type(s), price_list, dates, 
                                {'genome': s.genome} if hasattr(s, 'genome') else {}): s.NAME
                for s in strategies
            }
            for future in concurrent.futures.as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    res = future.result()
                    # Filter out dormant strategies that didn't trade (less than 1 rebalance/year)
                    if res['metrics']['num_rebalances'] < 5 and "B&H" not in name and "[BASE]" not in name:
                        continue
                        
                    results[name] = res
                    print(f"  Completed: {name:<35} | CAGR: {res['metrics']['cagr']*100:.1f}%")
                except Exception as e:
                    print(f"  Error running {name}: {e}")
        self.results.update(results)
        return results

    def run_resilience(self, samples_per_bucket: int = 10, target_strategies: list = None):
        """Standard resilience stress test - prints aggregate tables."""
        if self.data is None: self.load_data()
        strategies = target_strategies or self.discover_strategies()
        
        print(f"\nResilience test for: {[s.NAME for s in strategies]}")
        # Simplified resilience report for console
        for s in strategies:
            audit = _run_audit_batch(type(s), self.data, {'genome': s.genome} if hasattr(s, 'genome') else {}, iterations=samples_per_bucket * 5)
            print(f"  {s.NAME:<35} | Avg CAGR: {audit['avg_cagr']:>7.2f}% | Stability: {(audit['avg_cagr']/(s.on_data('test', self.data.iloc[0], None) or 1)):.0%}") # Dummy stability calc for console

    def print_results(self):
        if not self.results: return
        print("\n" + "=" * 95)
        print(f"  TOURNAMENT RESULTS ({self.start_date} -> {self.data.index[-1].date()})")
        print("=" * 95)
        print(f"  {'Strategy':<30} | {'CAGR':>8} | {'Sharpe':>8} | {'Max DD':>8} | {'Volat.':>8} | {'Trades':>6}")
        print("-" * 95)
        for name, res in sorted(self.results.items(), key=lambda x: x[1]["metrics"]["cagr"], reverse=True):
            m = res["metrics"]
            print(f"  {name:<30} | {m['cagr']*100:>7.2f}% | {m['sharpe']:>8.2f} | {m['max_dd']*100:>7.1f}% | {m['volatility']*100:>7.1f}% | {m['num_rebalances']:>6.0f}")
        print("=" * 95)

    def generate_report(self, output_path="results/report.html", skip_audits=False):
        if not self.results: return
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        report_data = []
        strategies = self.discover_strategies()
        strat_audits = {name: {} for name in self.results.keys()}
        
        if skip_audits:
            print("\n[AUDIT] Skipping robustness & synthetic tests as requested.")
        else:
            # Performance Optimization: 50 iterations is enough for a strong statistical hint
            ITERS = 50 
            print(f"\n[AUDIT] Starting Parallel Robustness & Synthetic tests ({ITERS} iterations per mode)...")
            print(f"  Note: Using deterministic seeding for fair & fast synthetic testing.")

            # Performance Optimization: Convert DataFrame to lightweight list ONCE
            # This prevents the 'OSError: handle is closed' by avoiding heavy Pandas serialization
            audit_records = self.data.to_dict('records')
            audit_dates = self.data.index.tolist()
            
            # 1. Schedule all audit tasks (Using lightweight records list)
            start_time = time.time()
            workers = max(1, (os.cpu_count() or 2) // 2)
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
                future_to_strat = {}
                for name, res in self.results.items():
                    strat_obj = next(s for s in strategies if s.NAME == name)
                    strat_type = type(strat_obj)
                    strat_kwargs = {'genome': strat_obj.genome} if hasattr(strat_obj, 'genome') else {}
                    
                    # Tag futures with start time
                    t0 = time.time()
                    f_res = executor.submit(_run_audit_batch, strat_type, audit_records, audit_dates, strat_kwargs, ITERS, 'resilience')
                    f_syn = executor.submit(_run_audit_batch, strat_type, audit_records, audit_dates, strat_kwargs, ITERS, 'synthetic')
                    
                    future_to_strat[f_res] = (name, 'resilience', t0)
                    future_to_strat[f_syn] = (name, 'synthetic', t0)

                completed = 0
                total = len(self.results) * 2
                for future in concurrent.futures.as_completed(future_to_strat):
                    name, mode, t_start = future_to_strat[future]
                    duration = time.time() - t_start
                    try:
                        strat_audits[name][mode] = future.result()
                    except Exception as e:
                        print(f"  Error in {mode} audit for {name}: {e}")
                    
                    completed += 1
                    # Show individual task completion time and strategy name
                    if completed % 5 == 0 or completed == total:
                        elapsed = time.time() - start_time
                        print(f"  [{completed}/{total}] {name} ({mode}) finished in {duration:.1f}s | Total: {elapsed:.1f}s")

        # 2. Assemble final report
        for name, res in self.results.items():
            report_data.append({
                "name": name,
                "metrics": res["metrics"],
                "resilience": strat_audits[name].get('resilience'),
                "synthetic": strat_audits[name].get('synthetic'),
                "curve": {
                    "dates": [str(d.date()) if hasattr(d, 'date') else str(d) for d, _ in res["portfolio"].equity_curve],
                    "equities": [float(e) for _, e in res["portfolio"].equity_curve]
                }
            })

        html = REPORT_TEMPLATE.replace("{{ DATA_JSON }}", json.dumps(report_data))
        with open(output_path, "w", encoding="utf-8") as f: f.write(html)
        print(f"\n[REPORT] Interactive tournament audit generated: {output_path}")
