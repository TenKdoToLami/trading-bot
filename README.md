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
```bash
# Run all strategies (full backtest since 1993)
python tests/run_tournament.py

# Run a single strategy
python tests/run_tournament.py --strategy "BEAST (SMA + RealVol)"

# Custom date range
python tests/run_tournament.py --start 2008-01-01 --end 2012-12-31

# Force refresh cached SPY data
python tests/run_tournament.py --refresh

# Skip interactive report generation
python tests/run_tournament.py --no-report

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

Record-breaking genomes are automatically saved to the `champions/v1_classic/vault/` directory.

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
- **Persistence**: Record-breaking genomes are saved to `champions/v2_multi/vault/` in real-time.

V2 results are also saved as `champions/v2_multi/genome.json`.


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
- **Persistence**: Record-breaking genomes are saved to `champions/v3_precision/vault/`.


### 6. Genome V4 — Adaptive Chameleon Evolution (New)
V4 introduces the "Chameleon" architecture. It replaces the complex scoring system of V3 with an environment-aware state machine that uses **Volatility Stretch** (VIX vs. its own EMA) to define regimes.

```bash
# Start evolution
python tests/run_evolution_v4.py --pop 100 --gen 50
```

#### How it Works: Environment-Aware Tiers
- **Dynamic Regimes**: Switches between `Calm`, `Stressed`, and `Panic` based on how far VIX is stretching from its long-term average.
- **Evolvable Parameters**:
  - `vix_ema`: The "memory" of market volatility (baseline).
  - `vol_stretch`: The threshold multiplier above baseline to trigger defensive modes.
  - `mom_period`: The lookback for the structural trend filter.
  - `rsi_period` & `rsi_entry`: Parameters for the "Aggressive Buy the Dip" logic during stress.
  - `lev_calm`: Targeted leverage during stability (e.g., 3.0x).
  - `lev_stress`: Reduced leverage when volatility spikes but trend holds (e.g., 1.0x).
  - `lev_panic`: Extreme defense when volatility spikes AND trend breaks (e.g., 0.0x).
- **Multi-Timeframe Resilience**: Optimized for robustness across the entire 30+ year SPY history.
- **Persistence**: Record-breaking genomes are saved to `champions/V4_CHAMELEON/vault/`.


### 7. Genome V4 Precision — 3-State AI Evolution (Alternative)
V4 Precision (V4P) evolves the same deep indicator logic as V3 but introduces a **Neutral State**. Instead of jumping between 3xSPY and CASH, it uses SPY as a baseline during moderate conditions.

```bash
# Evolve the 3-state AI
python tests/run_evolution_v4_precision.py --pop 300 --gen 100
```

#### How it Works: 3-State Logic
- **Three Regimes**: 
  - **Panic**: Triggered by the `panic` brain scoring above threshold -> **CASH**.
  - **Bullish**: Triggered by the `bull` brain scoring above threshold -> **3xSPY**.
  - **Neutral**: Default state when neither brain triggers -> **SPY**.


### 8. Genome V5 Sniper — Tiered Leverage Specialist (New)
The V5 architecture is a high-performance **Entry Hunter**. Unlike previous versions that hide in cash, the Sniper stays 100% invested in SPY as its baseline and use "fading" leverage to boost gains during bullish setups.

```bash
# Evolve the Tiered Sniper AI
python tests/run_evolution_v5_sniper.py --pop 300 --gen 100
```

#### How it Works: Tiered Logic
- **Baseline (1.0x SPY)**: Default state. No cash drag, always capturing market growth.
- **Moderate Snipe (2.0x SPY)**: Triggered when the AI brain score exceeds `t_low`.
- **Extreme Snipe (3.0x SPY)**: Triggered when the AI brain score exceeds `t_high`.
- **Fading Leverage**: As market signals fade, the strategy scales back from 3x -> 2x -> 1x, ensuring a smoother equity curve than binary switching.
- **Pure Growth**: This strategy has **no CASH state**. It is designed for investors who want to be 100% long at all times but with intelligent leverage scaling.


## 🛠️ Diagnostics & Strategy Audit
These tools help you verify the quality and resilience of your discovered strategies. All tools automatically detect if a genome is **V1, V2, V3, or V4**.

### 8. Vault Sweep — Cross-Regime Stress Test
Tests every genome in the vault across rolling 5-year windows (0–5yr, 5–10yr, ... 25–30yr) and ranks them by resilience.

```bash
# Sweep V4 Precision vault (The new 3-state AI)
python tests/vault_sweep.py --vault champions/v4_precision/vault

# Sweep V4 Chameleon vault (The gold standard)
python tests/vault_sweep.py --vault champions/V4_CHAMELEON/vault

# Sweep V3 vault
python tests/vault_sweep.py --vault champions/v3_precision/vault

# Sweep the V2 vault
python tests/vault_sweep.py --vault champions/v2_multi/vault
```

### 9. Genome X-Ray — Deep Behavioral Audit
Runs a single genome over the full inception period and produces a detailed breakdown of allocation behavior, including transition matrices and DNA visualization.

```bash
# X-Ray a champion (by path or name)
python tests/genome_xray.py champions/v4_precision/genome.json
python tests/genome_xray.py "Champion V4 (AI Precision)"
python tests/genome_xray.py "BEAST (SMA + RealVol)"
```
Reports include:
- **Tier Residency**: % of time in 3x/2x/1x/Cash, average & max streak lengths.
- **Leverage Distribution**: Visual histogram of daily leverage levels.
- **Switching Behavior**: Total rebalances, switches per year.
- **Genome DNA**: Active indicators, weights, and **Lookback Periods** (for V3).

### 10. Performance Audit — Institutional Report
Produces a bit-perfect terminal table of monthly/yearly returns and core risk metrics.

```bash
# Audit any strategy (auto-detects version)
python tests/performance_audit.py champions/v4_precision/genome.json
python tests/performance_audit.py "Buy & Hold 3x"
```

### 11. Resilience Showdown — The Champion Battle
Runs 100+ random historical periods (1–10 years) and counts how often each champion wins.

```bash
# Compare V4 Precision against V4 Chameleon
python tests/sweep_showdown.py champions/v4_precision/genome.json champions/V4_CHAMELEON/genome.json --matches 100
```

### 12. Monte Carlo Audit — Robustness Stress Test
The ultimate verification for V4. Generates 100+ "Alternative Timelines" by adding daily jitter, scaling volatility, and shifting macro signals. Calculates the true **Probability of Ruin**.

```bash
# Stress test V4 Precision
python tests/monte_carlo_audit.py champions/v4_precision/genome.json --iterations 100
python tests/monte_carlo_audit.py "Full Cash Panic"
```

### 13. Synthetic Data Tester — Anti-Overfitting Audit
Stitches together random blocks of historical data to ensure the strategy isn't "one-trick pony" that relies on a specific historical sequence.

```bash
# Run synthetic audit on V4 Precision
python tests/synthetic_audit.py "Champion V4 (AI Precision)" --iters 50 --chunk 252
```

### 14. Interactive Command Center
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

### 15. Output
- **Metrics table**: CAGR, Sharpe, Max Drawdown, Volatility, Trade count — printed to console.
- **Interactive Audit**: Once the tournament completes, it will automatically generate an interactive HTML report in `results/report.html` with sortable tables and Plotly charts.
- **Vault**: Optimal DNA matrices saved to `champions/vX/vault/`.

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
champions/              # Champion strategies and genomes
  v1_classic/           #   V1 AI
    genome.json
    strategy.py
    vault/              #   V1 Genome Collection
  v2_multi/             #   V2 Multi-Brain AI
    genome.json
    strategy.py
    vault/              #   V2 Genome Collection
  v3_precision/         #   V3 Precision AI
    genome.json
    strategy.py
    vault/              #   V3 Genome Collection
  V4_CHAMELEON/         #   V4 Adaptive Chameleon AI
    genome.json
    strategy.py
    vault/              #   V4 Genome Collection
  v1_manual/            #   Manual/Legacy config
    genome.json
    strategy.py

strategies/             # Strategy plugins
  base.py               #   Abstract interface
  beast_rvol.py         #   SMA + realized volatility tiers
  buy_and_hold_3x.py    #   Benchmark: always 3x
  buy_and_hold_spy.py   #   Benchmark: always 1x
  full_cash_panic.py    #   Binary: 3x bull / 100% cash panic
  genome_v2_strategy.py #   AI: Multi-Brain (3x/2x/1x/Cash)
  genome_v3_strategy.py #   AI: Precision Binary with Genetic Lookbacks
  genome_v4_precision.py #  AI: Precision 3-State (3x/1x/Cash)
  gene_v4_chameleon.py  #   AI: Adaptive Volatility & Momentum (Chameleon)

src/
  helpers/              # Shared utilities
    indicators.py       #   SMA, realized vol, drawdown
    data_provider.py    #   Local-first SPY data caching
  tournament/           # Control unit
    runner.py           #   Simulation orchestrator (T+1 lag model)
    portfolio.py        #   Holdings & return tracking
    evolution.py        #   Genetic Algorithm engine
  utils/                # Database utilities

tests/
  run_tournament.py     # CLI: full tournament
  run_evolution.py      # CLI: genetic algorithm V1
  run_evolution_v2.py   # CLI: genetic algorithm V2
  run_evolution_v3.py   #   CLI: genetic algorithm V3
  run_evolution_v4_precision.py # CLI: 3-state AI evolution
  run_evolution_v4.py   #   CLI: genetic algorithm V4
  vault_sweep.py        # CLI: cross-regime stress test
  sweep_showdown.py     # CLI: V1 vs V2 resilience showdown
  performance_audit.py  # CLI: institutional performance report
  genome_xray.py        # CLI: deep genome behavioral audit
  generate_viz_data.py  # CLI: generate visualizer data

vault/                  # V1 Genomes
vault_v2/               # V2 Genomes
vault_v3/               # V3 Genomes
champions/V4_CHAMELEON/vault/ # V4 Genomes
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
| **Chameleon V4 (AI)** | **Current Meta**: Adaptive volatility state machine using VIX-Stretch and Momentum filters. |
| **Genome Strategy** | AI-bred strategy using **Dual-State** (Panic/Base) logic, Ablation (Feature Selection), and Rebalance Lockouts. |
| **Full Cash Panic** | Same SMA regime, but 100% cash during any panic. |
| **Buy & Hold 3x** | Pure 3x leveraged buy-and-hold benchmark. |
| **Buy & Hold SPY** | Plain 1x index benchmark. |
| **Equal Combos (20d)** | Various combinations of 1x, 2x, 3x SPY and CASH, rebalanced every 20 days. |
| **Indicator Exits** | 3x SPY strategies that exit to 100% CASH based on RSI, MACD, EMA, etc. |

