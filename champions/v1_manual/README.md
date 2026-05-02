# V1 Manual — The Discrete Alpha Baseline

## 🧠 Strategy Logic
The evolved version of the original "Golden Rules." While the structure remains a discrete VIX-bracketed decision engine, it is now fully evolution-capable, allowing the AI to find the optimal "market switch" points.

### 🔬 Decision Engine Anatomy
1.  **Trend Filter (SMA)**: Uses a Simple Moving Average lookback (Evolved: ~290 days) to determine if the market is investable.
2.  **Discrete VIX Brackets**: Segments market volatility into 4 distinct regimes.
3.  **Hysteresis/Safety**: Implements a `min_b_days` (Bond Days) lock to prevent rapid rebalancing during high volatility.
4.  **Binary Aggression**: Favors 3x SPY during bull runs and rapid retreats to CASH.

---

## ⚡ QUICK LAUNCH: V1 Manual Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_v1_manual.py --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_v1_manual.py --pop 100 --gen 100 --vault champions/v1_manual/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v1_manual/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v1_manual/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v1_manual/vault --promote  --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate. Use `0.35 - 0.50` for aggressive jumps when seeding. |
| `--vault`| `None` | Path to load seeds from. |

---

## 🛡️ Best Used For
The "Aggression Benchmark." While V10 offers better risk-adjusted returns, V1 Manual represents the raw power of discrete market switching. It is the target that all neural models must beat in terms of raw CAGR.
