# 🧬 V9 Intra-Day Confidence (Real-Time Risk Management)

## 📡 Strategy Overview
V9 Intra is an evolution of the V9 architecture designed for **Same-Day Execution**. While standard V9 observes the market and trades the next day, V9 Intra uses a "Live Trigger" to respond to price moves while the market is still open.

### 🔬 Decision Engine Anatomy
1.  **14-Feature Neural Net**: Ingests 13 standard macro/technical indicators PLUS a 14th "Intraday Delta" feature.
2.  **Live Trigger Logic**: (Today Mid-Price / Yesterday Close). This allows the model to "Panic Sell" or "Aggressive Buy" mid-day.
3.  **Same-Day Rebalancing**: Rebalances occur at the mid-day TWAP price based on the signal generated at that same price point.
4.  **Surgical DD Ceiling**: Evolved with a non-linear penalty for drawdowns exceeding 35%.

---

## ⚡ QUICK LAUNCH: V9 Intra Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v9_intra --pop 200 --gen 100` |
| **Seed from V9** | `python tests/run_evolution_universal.py --version v9_intra --pop 500 --gen 100 --vault champions/v9_confidence/vault --tournament` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v9_intra/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v9_intra/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v9_intra/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
- **Fitness**: `CAGR - (DD * 0.3)` with exponential penalty for DD > 35%.
- **Architecture**: 14-Input MLP with Confidence Smoothing and Hysteresis.
