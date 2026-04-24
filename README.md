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

## ⚙️ Logic Components
- **SMA Climate Control**: Only takes aggressive leverage when SPY is above its SMA.
- **VIX Gearbox**: Dynamically shifts between 1x, 2x, and 3x leverage based on volatility levels.
- **Base Lockout**: When entering the most aggressive Bull Tier (0), the bot locks into that state for a set period to avoid whipsaw.

## 📂 Project Structure
- `main.py`: Daily entry point.
- `src/engine.py`: Core strategy calculations.
- `src/manager.py`: Stateful filters and timers.
- `src/alpaca.py`: API client and rebalancing logic.
- `src/db_manager.py`: Database operations.
- `data/`: Local storage for the SQLite database.
