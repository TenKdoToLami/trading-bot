# V11 Seasonal — The Macro-Temporal Engine

## 🧠 Strategy Logic
V11 Seasonal is an institutional-grade evolution of the neural architecture. It bridges the "information gap" by incorporating macroeconomic credit signals and temporal market patterns into a high-dimensional deep neural network. Unlike previous versions, V11 understands the *context* of time and institutional credit stress.

### 🔬 Decision Engine Anatomy
1.  **Temporal Intelligence**: Specifically engineered to recognize the **Turn-of-the-Month** effect and seasonal cycles (e.g., "Santa Claus Rally" vs "September Slump") using trigonometric encoding.
2.  **Credit Regime Detection**: Monitors the **BAA10Y Credit Spread** to detect institutional liquidity stress before it translates into equity price action.
3.  **Expanded Neural Brain**: Features an upgraded 18-input architecture (18 -> 32 -> 4) designed to synthesize technical, macro, and temporal signals simultaneously.
4.  **Intra-Day Confidence**: Inherits the high-frequency awareness of V9, allowing it to react to same-day price deltas while maintaining macro-level perspective.

---

## ⚡ QUICK LAUNCH: V11 Seasonal Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v11_seasonal --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v11_seasonal --pop 100 --gen 100 --vault champions/v11_seasonal/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v11_seasonal/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v11_seasonal/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v11_seasonal/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size (recommended 100+ for 18-input space). |
| `--gen` | `100` | Number of generations (requires more time to converge). |
| `--mut` | `0.20` | Mutation rate (adjusts weight/bias variance). |
| `--vault` | `None` | Path to load seeds from. |

---

## 📊 Feature Set (18 Inputs)
- **1-13**: Standard Technicals (SMA, EMA, RSI, MACD, ADX, TRIX, Slope, Vol, ATR, VIX, YC, MFI, BBW)
- **14**: **Credit Spread (BAA10Y)**
- **15-16**: **Month Cycle (Sin/Cos)**
- **17**: **Turn-of-the-Month Flag**
- **18**: **Intraday Return**

---

## 🛡️ Best Used For
The "Institutional Strategist." V11 is designed for multi-decade stability. By accounting for the credit market and seasonality, it aims to avoid the "volatility traps" that often trip up purely technical models.
