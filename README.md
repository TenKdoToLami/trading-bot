# Tactical Bot — Strategy Tournament Framework

A specialized framework for backtesting and evolving high-leverage tactical strategies against SPY.

## 🏗 Architecture

The framework is built around three core engines:
- **Strategy Plugins** (`strategies/`): Each strategy is an independent file that receives one day of SPY data at a time and returns holding decisions.
- **Control Unit** (`src/tournament/`): Feeds data, tracks portfolio state, enforces rules, and computes performance metrics.
- **Helpers** (`src/helpers/`): Shared indicator functions (SMA, realized volatility) and local-first data loading.

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Tournament
The tournament runner is the primary tool for evaluating all champions and benchmarks.
```bash
# Run all strategies (full backtest since 1993)
python tests/run_tournament.py

# Run a single strategy
python tests/run_tournament.py --strategy "Champion V6 (Balancer)"

# Custom date range
python tests/run_tournament.py --start 2008-01-01 --end 2012-12-31

# Force refresh cached SPY data
python tests/run_tournament.py --refresh

# Skip interactive report generation
python tests/run_tournament.py --no-report

# Resilience stress test — random periods across duration buckets
python tests/run_tournament.py --resilience --samples 20
```

#### ⚙️ Tournament Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--strategy` | `None` | Case-insensitive strategy name. Supports comma-separated list. |
| `--start` | `1993-01-01` | Backtest start date. |
| `--end` | `Latest` | Backtest end date. |
| `--refresh` | `Off` | Force re-download of SPY/VIX data from yfinance. |
| `--no-report`| `Off` | Skip generation of Plotly/HTML reports. |
| `--resilience`| `Off` | **Stress Test**: Samples random periods across 5-30yr buckets. |
| `--samples` | `10` | Number of random samples per bucket in Resilience mode. |
| `--no-audit` | `Off` | Skip the heavy Robustness/Synthetic data audit phase. |

---

## 🏆 God Mode Variants (Mathematical Limits)

These "God Mode" strategies use lookahead and Dynamic Programming to calculate the mathematically perfect holding sequence. They serve as the **absolute upper bound** of performance under specific constraints.

| Strategy | Constraint | Purpose |

|----------|------------|---------|
| `Most Optimal (God Mode)` | None | The theoretical maximum return with daily rebalancing. |
| `[Cheat] Guided God (Weekly)` | 5 Trading Days | Optimal path if trades are locked for a full week. |
| `[Cheat] Patient God (Monthly)` | 21 Trading Days | Optimal path if trades are locked for a full month. |
| `[Cheat] Eternal God (Yearly)` | 252 Trading Days | Optimal path if trades are locked for a full year. |

**Example Usage:**
```bash
# Compare the theoretical weekly limit against your AI
python tests/run_tournament.py --strategy "[Cheat] Guided God (Weekly),Champion V6 (Balancer)"
```

---

## 🧬 Evolutionary Strategy Breeding
The framework includes several Genetic Algorithm (GA) engines to autonomously discover optimal indicator combinations and weights.

### Evolution Commands
| Command | Version | Goal |
|---------|---------|------|
| `python tests/run_evolution_v6_balancer.py` | **V6** | Probabilistic Softmax Allocator (Institutional Grade) |
| `python tests/run_evolution_v5_sniper.py`   | **V5** | Tiered Entry Hunter (1x -> 2x -> 3x) |
| `python tests/run_evolution_v4_precision.py`| **V4** | Precision 3-State AI (CASH/1x/3x) |
| `python tests/run_evolution_v4_chameleon.py`| **V4** | Adaptive Chameleon (Volatility Regime Selection) |
| `python tests/run_evolution_v3_precision.py`| **V3** | Binary AI with Genetic Lookback Optimization |
| `python tests/run_evolution_v2_multi.py`    | **V2** | Multi-Brain Multi-Regime Logic |
| `python tests/run_evolution_v1_classic.py`  | **V1** | Classic Linear Weight-Sum (Baseline) |

### Common Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 30-500 | Population size. Higher = more diversity, slower generations. |
| `--gen` | 10-200 | Number of generations to evolve. |
| `--mut` | 0.15 | Mutation rate. Use `0.25 - 0.40` when seeding from a vault. |
| `--seed`| None | Path to a `vault/` directory to load initial genomes from. |
| `--ablation` | `Off` | Feature Selection: Disables indicators randomly to find the most robust subset. |
| `--min-cagr`| `0.0` | **Performance Floor**: Ignores any genome with CAGR lower than this (e.g., `0.35` for 35%). |

---

## 🛠️ Diagnostics & Strategy Audit
These tools help you verify the quality and resilience of your discovered strategies. All tools automatically detect the strategy version (V2–V6).

### 1. Vault Sweep — Cross-Regime Stress Test
Tests every genome in a vault across rolling windows (5yr to 30yr) to rank them by resilience. 
*   Use `--promote` to automatically update the main champion `genome.json` with the #1 winner.
*   Use `--top X` to **prune** the vault, retaining only the Top X performers and deleting the rest.

```bash
# Audit and promote the best performer
python tests/vault_sweep.py --vault champions/v6_balancer/vault --promote

# Prune vault to keep only the Top 20 most resilient genomes
python tests/vault_sweep.py --vault champions/v7_deep_fluid/vault --top 20
```

### 2. Genome X-Ray — Behavioral Audit
Runs a deep simulation and produces a breakdown of allocation behavior, transition matrices, and DNA visualization.
```bash
python tests/genome_xray.py champions/v6_balancer/genome.json
```

### 3. Performance Audit — Institutional Report
Produces a terminal table of monthly/yearly returns and core risk/drawdown metrics.
```bash
python tests/performance_audit.py champions/v6_balancer/genome.json
```

### 4. Monte Carlo Audit — Robustness Stress Test
Generates "Alternative Timelines" with daily jitter and volatility scaling to calculate the **Probability of Ruin**.
```bash
python tests/monte_carlo_audit.py champions/v6_balancer/genome.json --iterations 100
```

### 5. Synthetic Data Tester — Anti-Overfitting
Stitches together random blocks of historical data to ensure the strategy isn't "overfit" to a specific chronological sequence.
```bash
python tests/synthetic_audit.py "Champion V6 (Balancer)" --iters 50 --chunk 252
```

---

## 🧩 Writing a New Strategy

Create a new `.py` file in `strategies/` that subclasses `BaseStrategy`:

```python
from strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    NAME = "My Custom Strategy"

    def __init__(self):
        self.reset()

    def reset(self):
        self.prices = []

    def on_data(self, date, price_data, prev_data):
        # price_data contains finalized OHLCV + VIX + Indicators
        return {"3xSPY": 1.0} # Return holdings dict or None
```

---

## 📂 Project Structure
```
champions/              # Active genome.json champions and historical vaults
strategies/             # Strategy logic plugins (genome_vX_name.py)
src/tournament/         # Core engines: Runner, Portfolio, Evolution
src/helpers/            # Indicators and Data Providers
tests/                  # CLI tools for Tournament, Evolution, and Audits
data/                   # Cached market data
results/                # Tournament HTML reports and Plotly charts
visualizer/             # Browser-based Interactive Command Center
```
