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
```

### 3. Output
- **Metrics table**: CAGR, Sharpe, Max Drawdown, Volatility, Trade count — printed to console.
- **Equity chart**: Saved to `results/tournament_chart.png`.

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

    def on_data(self, date, spy_price):
        self.prices.append(spy_price)
        # ... your logic here ...

        # Return None to hold, or a dict to rebalance:
        return {"3xSPY": 0.5, "CASH": 0.5}
```

**Rules:**
- You only receive `(date, spy_price)` — no other market data.
- If you need indicators (SMA, volatility), compute them from your accumulated prices using `src.helpers.indicators`.
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

src/
  helpers/              # Shared utilities
    indicators.py       #   SMA, realized vol, drawdown
    data_provider.py    #   Local-first SPY data caching
  tournament/           # Control unit
    runner.py           #   Simulation orchestrator
    portfolio.py        #   Holdings & return tracking
  execution/            # Alpaca live trading (future)
  utils/                # Database utilities

tests/
  run_tournament.py     # CLI entry point

config/                 # API keys, strategy DNA
data/                   # Cached market data (auto-generated)
results/                # Tournament output (charts)
```

## ⚙️ Included Strategies

| Strategy | Description |
|---|---|
| **BEAST (SMA + RealVol)** | SMA regime detection + realized volatility tiers. 3x in bull, tiered allocation in panic. |
| **Full Cash Panic** | Same SMA regime, but 100% cash during any panic. |
| **Buy & Hold 3x** | Pure 3x leveraged buy-and-hold benchmark. |
| **Buy & Hold SPY** | Plain 1x index benchmark. |
