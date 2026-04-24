# Tactical Leverage Paper Trading Bot

A standalone execution engine for the BEAST/SHIELD tactical strategies. This bot syncs with Alpaca Paper Trading to automate multi-tier leverage management based on volatility regimes.

## 🏗 Architecture
- **Stateless Engine**: Translates market data (SPY/VIX) into target leverage tiers.
- **Stateful Manager**: Handles SMA delays, sticky tier timers, and the **Base Lockout** logic.
- **Executioner**: Automates liquidation and rebalancing on Alpaca.
- **Persistence**: SQLite database tracks historical prices and internal timers.

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configuration
Copy `.env.example` to `.env` and fill in your Alpaca API credentials.
```bash
cp .env.example .env
```

### 3. Strategy DNA
Place your optimized DNA file in the root directory as `strategy.json`.

### 4. Run Daily
Execute the bot once a day after market close (e.g., 4:15 PM EST).
```bash
python main.py
```

python main.py --dry-run
```

## 🐧 Linux Server Deployment
To run the bot 24/7 on a Linux server:

1. **Make the manager executable**:
   ```bash
   chmod +x manage.sh
   ```

2. **Management Commands**:
   ```bash
   sudo ./manage.sh install    # Setup and start background service
   sudo ./manage.sh status     # Check if bot is alive
   sudo ./manage.sh logs       # Stream the live sync logs
   sudo ./manage.sh uninstall  # Completely remove the service
   ```

### 6. Quick CLI (Account Status)
```bash
python cli.py cash       # Check buying power
python cli.py bal        # Check total value (Balance)
python cli.py open       # Check market status
python cli.py pos        # Check current holdings (Positions)
python cli.py vix        # Check signal price
python cli.py liquidate  # Emergency exit (Confirm req)
```

## ⚙️ Logic Components
- **SMA Climate Control**: Only takes aggressive leverage when SPY is above its SMA.
- **VIX Gearbox**: Dynamically shifts between 1x, 2x, and 3x leverage based on volatility levels.
- **Base Lockout**: When entering the most aggressive Bull Tier (0), the bot locks into that state for a set period to avoid whipsaw.

## 📂 Project Structure
- `main.py`: Daily entry point.
- `config/`: Strategy DNA (`strategy.json`) and `.env.example`.
- `src/core/`: Decision engine and regime management.
- `src/execution/`: Alpaca API integration.
- `src/utils/`: Database and persistence utilities.
- `tests/`: Long-term theory and resilience tests.
- `data/`: Local SQLite storage.

## 🛠 Manual Execution & SDK
You can use the `AlpacaClient` as a standalone SDK for manual operations or testing.

### 1. Initialize Client
```python
from src.execution.alpaca import AlpacaClient
alpaca = AlpacaClient()
```

### 2. Market Data & Account
```python
equity = alpaca.get_equity()      # Get total account value
cash = alpaca.get_cash()          # Get available buying power
open = alpaca.is_market_open()    # Returns True if NYSE is open
price = alpaca.get_price("VOO")   # Get latest signal price
pos = alpaca.get_positions()      # Get current managed holdings
```

### 3. Manual Trading
```python
# Buy $1000 worth of SPXL
alpaca.buy_dollars("SPXL", 1000)

# Emergency Liquidation of a specific ticker
alpaca.sell_all("SSO")

# Liquidate all managed assets (2x/3x/Cash)
alpaca.liquidate_managed_assets()

```
