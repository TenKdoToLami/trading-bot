# Tactical Bot — Strategy Tournament & Trading Framework

A dual-purpose framework for backtesting leverage strategies against SPY and (eventually) executing the winning strategy via Alpaca paper trading.

## 🏗 Architecture

The framework is split into two halves:

### Tournament (Backtesting)
- **Strategy Plugins** (`strategies/`): Each strategy is an independent file that receives one day of SPY data at a time and returns holding decisions.
- **Control Unit** (`src/tournament/`): Feeds data, tracks portfolio state, enforces rules, and computes performance metrics.
- **Helpers** (`src/helpers/`): Shared indicator functions (SMA, realized volatility) and local-first data loading.

### Live Trading (Future)
- **Executioner** (`src/execution/`): Alpaca API integration for automated rebalancing.
- **Persistence** (`src/utils/`): SQLite for state tracking.

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Tournament
```bash
# Run all strategies (full backtest since 1993)
python tests/run_tournament.py

# Run a single strategy
python tests/run_tournament.py --strategy "BEAST (SMA + RealVol)"

# Custom date range
python tests/run_tournament.py --start 2008-01-01 --end 2012-12-31

# Force refresh cached SPY data
python tests/run_tournament.py --refresh

# Skip chart generation
python tests/run_tournament.py --no-chart

# Resilience stress test — random periods across duration buckets
python tests/run_tournament.py --resilience

# python tests/run_tournament.py --resilience --samples 20
```

### 3. Evolutionary Strategy Breeding
The framework includes a Genetic Algorithm engine to autonomously discover optimal indicator combinations.
```bash
# Cold start: pure random population
python tests/run_evolution.py --pop 200 --gen 100

# Warm seeded: inject top vault performers into the initial population
python tests/run_evolution.py --pop 500 --gen 100 --seed vault

# Fine-tuning with higher mutation (recommended when seeding)
python tests/run_evolution.py --pop 500 --gen 100 --seed vault --mut 0.25
```

| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 30 | Population size |
| `--gen` | 10 | Number of generations |
| `--mut` | 0.15 | Mutation rate (0.25 recommended with `--seed`) |
| `--seed` | None | Path to vault directory to seed with top performers |

Record-breaking genomes are automatically saved to the `vault/` directory.

- The best vault genomes (sorted by CAGR) are injected first.

### 4. Genome V2 — Multi-Brain Evolution (Experimental)
V2 introduces "Tier-Specific Brains." Unlike V1, which uses a single weight matrix for all bull decisions, V2 evolves independent weights and thresholds for each target leverage tier (3x, 2x, 1x) and a dedicated "Panic" brain.

```bash
# Cold start (random population)
python tests/run_evolution_v2.py --pop 500 --gen 100

# Seeding from previous champions (highly recommended)
python tests/run_evolution_v2.py --pop 1000 --gen 200 --seed vault_v2 --mut 0.3

# High-residency fine-tuning (reward staying in 1x/2x instead of binary 3x/Cash)
python tests/run_evolution_v2.py --pop 500 --gen 100 --push-mid
```

#### CLI Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 50 | Population size. Higher = more diversity, slower generations. |
| `--gen` | 20 | Number of generations to evolve. |
| `--mut` | 0.15 | Mutation rate. Use `0.25 - 0.40` when seeding from a vault. |
| `--seed` | None | Path to a directory (e.g., `vault_v2`) to load initial genomes from. |
| `--push-mid` | `False` | **Residency Bonus**: Adds fitness points for time spent in 1x and 2x tiers to reduce volatility. |
| `--no-ablation` | `False` | Disables indicator ablation (forces all indicators to be active). |

#### How it Works: Multi-Brain Architecture
- **State Selection**: The strategy evaluates four independent "brains" simultaneously: `panic`, `3x`, `2x`, and `1x`.
- **Thresholding**: Each brain produces a score based on its unique weights. The highest-tier brain whose score exceeds its evolved threshold determines the day's allocation.
- **Fitness Scoring**: The engine optimizes for `(CAGR * 100) - (MaxDD * 10)`. 
- **Safety Valve**: Any genome hitting a drawdown of >95% is immediately discarded (fitness = -9999).
- **Persistence**: Record-breaking genomes are saved to `vault_v2/` in real-time.

V2 results are also saved as `best_genome_v2.json` in the root directory.


### 5. Genome V3 — Precision Binary Evolution (Experimental)
V3 focuses entirely on the 3xSPY vs CASH decision, abandoning mid-tier scaling. Instead of using hardcoded indicator timeframes, V3 evolves the **Lookback Periods** for every indicator independently for its two specialized brains (Panic vs Bull).

```bash
# Cold start (random population)
python tests/run_evolution_v3.py --pop 1000 --gen 200

# Seeding from previous V3 champions
python tests/run_evolution_v3.py --pop 1000 --gen 200 --seed vault_v3 --mut 0.3
```

#### How it Works: Binary Architecture & Dynamic Lookbacks
- **Dual Brains**: `panic` (evaluates first, forces CASH) and `bull` (evaluates second, votes for 3xSPY).
- **Per-Brain Lookbacks**: The GA mutates the lookback ranges (e.g., SMA 20-300, RSI 5-50) uniquely for each brain, allowing the `panic` brain to be highly reactive while the `bull` brain remains macro-focused.
- **Pure Alpha Focus**: Fitness is simply `(CAGR * 100) - (MaxDD * 10)`.
- **Persistence**: Record-breaking genomes are saved to `vault_v3/`.


## 🛠️ Diagnostics & Strategy Audit
These tools help you verify the quality and resilience of your discovered strategies. All tools automatically detect if a genome is **V1, V2, or V3**.

### 6. Vault Sweep — Cross-Regime Stress Test
Tests every genome in the vault across rolling 5-year windows (0–5yr, 5–10yr, ... 25–30yr) and ranks them by resilience.

```bash
# Sweep V3 vault (recommended)
python tests/vault_sweep.py --vault vault_v3

# Sweep the V2 vault
python tests/vault_sweep.py --vault vault_v2 --samples 15
```

### 7. Genome X-Ray — Deep Behavioral Audit
Runs a single genome over the full inception period and produces a detailed breakdown of allocation behavior, including transition matrices and DNA visualization.

```bash
# X-Ray a V3 champion
python tests/genome_xray.py vault_v3/v3_cagr_52.12_dd_-42.15.json
```
Reports include:
- **Tier Residency**: % of time in 3x/2x/1x/Cash, average & max streak lengths.
- **Leverage Distribution**: Visual histogram of daily leverage levels.
- **Switching Behavior**: Total rebalances, switches per year.
- **Genome DNA**: Active indicators, weights, and **Lookback Periods** (for V3).

### 8. Performance Audit — Institutional Report
Produces a bit-perfect terminal table of monthly/yearly returns and core risk metrics.

```bash
# Audit a genome (auto-detects version)
python tests/performance_audit.py vault_v3/v3_cagr_52.12_dd_-42.15.json
```

### 9. Resilience Showdown — The Champion Battle
Runs 100+ random historical periods (1–10 years) and counts how often each champion wins.

```bash
# Compare a V2 champ against a V3 champ
python tests/sweep_showdown.py vault_v2/v2_best.json vault_v3/v3_best.json --matches 100
```

### 10. Monte Carlo Audit — Robustness Stress Test
The ultimate verification for V3. Generates 100+ "Alternative Timelines" by adding daily jitter, scaling volatility, and shifting macro signals. Calculates the true **Probability of Ruin**.

```bash
# Stress test a V3 champion
python tests/monte_carlo_audit.py vault_v3/v3_cagr_43.51_dd_-69.28.json --iterations 100
```

### 11. Interactive Command Center
A browser-based dashboard for visual backtesting with time-travel capabilities.
```bash
# Generate the latest simulation data
# (Ensure you are using the correct script for your current strategy)
python tests/run_tournament.py --strategy "Genome V2 (Multi-Brain)"

# Open in browser
start visualizer/index.html
```


Features:
- **4-Chart Grid**: Macro (log), Relative, Zoomed Equity, and Price vs SMA
- **Multi-Benchmark**: Bot vs 1x VOO, 2x SSO, 3x UPRO
- **Time Travel**: Pick any start date to re-index all curves to 1.00x
- **Live Simulation**: Press PLAY to watch the bot navigate 30 years of history
- **Risk Telemetry**: Real-time drawdown, VIX, tier tracking, and tactical grid

### 11. Output
- **Metrics table**: CAGR, Sharpe, Max Drawdown, Volatility, Trade count — printed to console.
- **Equity chart**: Saved to `results/tournament_chart.png`.
- **Vault**: Optimal DNA matrices saved to `vault/genome_cagr_X_dd_Y.json`.

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
        # ... reset any internal state

    def on_data(self, date, price_data, prev_data):
        spy_price = price_data['close']
        self.prices.append(spy_price)
        # ... your logic here ...

        # Return None to hold, or a dict to rebalance:
        return {"3xSPY": 1.0}
```

**Rules:**
- **Execution:** All trades execute at the Average price (`(Open + Close) / 2`) of the **next day** (T+1) to ensure zero look-ahead bias.
- **Data:** `price_data` contains the full finalized OHLCV for the current day.
- **History:** `prev_data` contains the finalized data for the previous day.
- Allowed assets: `SPY`, `2xSPY`, `3xSPY`, `CASH`.
- Holdings weights must sum to `1.0`.
- Return `None` if no rebalance is needed.

## 📂 Project Structure
```
strategies/             # Strategy plugins (one file per strategy)
  base.py               #   Abstract interface
  beast_rvol.py         #   SMA + realized volatility tiers
  buy_and_hold_3x.py    #   Benchmark: always 3x
  buy_and_hold_spy.py   #   Benchmark: always 1x
  full_cash_panic.py    #   Binary: 3x bull / 100% cash panic
  genome_v2_strategy.py #   AI: Multi-Brain (3x/2x/1x/Cash)
  genome_v3_strategy.py #   AI: Precision Binary with Genetic Lookbacks

src/
  helpers/              # Shared utilities
    indicators.py       #   SMA, realized vol, drawdown
    data_provider.py    #   Local-first SPY data caching
  tournament/           # Control unit
    runner.py           #   Simulation orchestrator (T+1 lag model)
    portfolio.py        #   Holdings & return tracking
    evolution.py        #   Genetic Algorithm engine
  execution/            # Alpaca live trading (future)
  utils/                # Database utilities

tests/
  run_tournament.py     # CLI: full tournament
  run_evolution.py      # CLI: genetic algorithm V1
  run_evolution_v2.py   # CLI: genetic algorithm V2
  run_evolution_v3.py   # CLI: genetic algorithm V3
  vault_sweep.py        # CLI: cross-regime stress test
  sweep_showdown.py     # CLI: V1 vs V2 resilience showdown
  performance_audit.py  # CLI: institutional performance report
  genome_xray.py        # CLI: deep genome behavioral audit
  generate_viz_data.py  # CLI: generate visualizer data

vault/                  # V1 Genomes
vault_v2/               # V2 Genomes
vault_v3/               # V3 Genomes
visualizer/             # Interactive Command Center dashboard
  index.html            #   Browser-based UI
  data.js               #   Generated simulation data (gitignored)
  config.js             #   Generated strategy config (gitignored)
config/                 # API keys, strategy DNA
data/                   # Cached market data (auto-generated)
results/                # Tournament output (charts)
```

## ⚙️ Included Strategies

| Strategy | Description |
|---|---|
| **BEAST (SMA + RealVol)** | SMA regime detection + realized volatility tiers. 3x in bull, tiered allocation in panic. |
| **Genome Strategy** | AI-bred strategy using **Dual-State** (Panic/Base) logic, Ablation (Feature Selection), and Rebalance Lockouts. |
| **Full Cash Panic** | Same SMA regime, but 100% cash during any panic. |
| **Buy & Hold 3x** | Pure 3x leveraged buy-and-hold benchmark. |
| **Buy & Hold SPY** | Plain 1x index benchmark. |
| **Equal Combos (20d)** | Various combinations of 1x, 2x, 3x SPY and CASH, rebalanced every 20 days. |
| **Indicator Exits** | 3x SPY strategies that exit to 100% CASH based on RSI, MACD, EMA, etc. |

