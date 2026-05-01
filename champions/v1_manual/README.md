# V1 Manual — The SMA/VIX Baseline

## 🧠 Strategy Logic
The original "Golden Rules" of tactical trading. This is a non-evolved, rule-based strategy used as the foundation for the entire project.

### 🔬 Decision Engine Anatomy
1.  **Trend Verification**: Checks if the current price is above the **200-day Simple Moving Average (SMA)**. If below, the market is deemed "uninvestable."
2.  **Volatility Threshold (VIX)**: If the VIX exceeds **30.0**, triggers an immediate "Panic" signal, overriding all other indicators.
3.  **Yield Curve Filter**: Monitors the spread between long and short-term debt; if inverted, restricts allocation to defensive levels.
4.  **Static Execution**: Unlike evolved versions, these rules are hardcoded and do not adapt to historical noise or changing market micro-structures.

### 📈 Leverage States
- **CASH / 1x / 3x**

## 🛡️ Best Used For
The "Stable Benchmark." All AI versions must beat the V1 Manual returns and Sharpe to be considered valid.
