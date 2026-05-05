# 🧬 V9 Intra-Day Confidence (Real-Time Risk Management)

## 📡 Strategy Overview
V9 Intra is an evolution of the V9 architecture designed for **Same-Day Execution**. While standard V9 observes the market and trades the next day, V9 Intra uses a "Live Trigger" to respond to price moves while the market is still open.

### 🔬 Decision Engine Anatomy
1.  **14-Feature Neural Net**: Ingests 13 standard macro/technical indicators PLUS a 14th "Intraday Delta" feature.
2.  **Live Trigger Logic**: (Today Mid-Price / Yesterday Close). This allows the model to "Panic Sell" or "Aggressive Buy" mid-day.
3.  **Same-Day Rebalancing**: Rebalances occur at the mid-day TWAP price based on the signal generated at that same price point.
4.  **Surgical DD Ceiling**: Evolved with a non-linear penalty for drawdowns exceeding 35%.

---

## 🛠️ Feature Matrix & Indicators
The strategy utilizes a 14-dimensional input vector, normalized to assist neural network convergence.

| # | Indicator | Lookback | Description | Normalization Formula |
|---|---|---|---|---|
| 1 | **SMA Delta** | 200 | Distance from long-term trend | `((Price - SMA) / SMA) * 5` |
| 2 | **EMA Delta** | 50 | Distance from medium-term trend | `((Price - EMA) / EMA) * 10` |
| 3 | **RSI** | 14 | Momentum oscillator | `(RSI - 50) / 50` |
| 4 | **MACD** | 12/26 | Trend momentum | `(MACD / Price) * 100` |
| 5 | **ADX** | 14 | Trend strength | `(ADX - 25) / 25` |
| 6 | **TRIX** | 15 | Triple-smoothed EMA rate of change | `TRIX` (Raw) |
| 7 | **LinReg Slope** | 20 | Linear regression slope | `(Slope / Price) * 1000` |
| 8 | **Volatility** | 20 | Realized annualized volatility | `Volatility * 5` |
| 9 | **ATR** | 14 | Average True Range (normalized) | `(ATR / Price) * 50` |
| 10| **VIX** | Live | Market Fear Index | `(VIX - 20) / 10` |
| 11| **Yield Curve** | Live | 10Y-3M Treasury Spread | `YieldCurve` (Raw) |
| 12| **MFI** | 14 | Money Flow Index (Volume + Price) | `(MFI - 50) / 50` |
| 13| **BB Width** | 20 | Bollinger Band Width | `BBW * 10` |
| 14| **Intraday Ret**| Live | **THE TRIGGER**: Mid-day % change | `((MidPrice - PrevClose) / PrevClose) * 20` |

---

## 🧠 Neural Architecture
The brain of V9 Intra is a Multi-Layer Perceptron (MLP) evolved through neuro-evolution.

- **Input Layer**: 14 neurons (Normalized Features).
- **Hidden Layer**: 24 neurons with **ReLU** activation.
- **Output Layer**: 4 neurons with **Softmax** activation.
- **States**: 
    - `0`: Cash (100% Liquidity)
    - `1`: 1x SPY (Unleveraged)
    - `2`: 2x SPY (Leveraged)
    - `3`: 3x SPY (Ultra Leveraged)

### 🌊 Signal Processing
To prevent "whipsawing" (excessive trading), two layers of stability are applied:
1.  **Confidence Smoothing**: Alpha-based exponential moving average of output probabilities (Default `α = 0.5`).
2.  **Hysteresis Buffer**: A state change only triggers if the new state's confidence exceeds the current state's confidence by a fixed margin (Default `H = 0.15`).

---

## ⚡ QUICK LAUNCH: V9 Intra Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v9_intra --pop 100 --gen 100` |
| **Seed from V9** | `python tests/run_evolution_universal.py --version v9_intra --pop 500 --gen 100 --vault champions/v9_intra/vault --tournament` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v9_intra/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v9_intra/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v9_intra/vault --promote --top 20` |

---
