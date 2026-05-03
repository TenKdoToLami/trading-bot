# V3 Precision — The Aggressive Switcher

## 🧠 Strategy Logic
V3 is a highly optimized **Binary State Machine**. It is the first version to use Genetic evolution for both indicator weights and thresholds, focusing on a clean "Full Risk" vs "Full Safety" profile.

### 🔬 Decision Engine Anatomy
1.  **Dual-Brain Scoring**: Simultaneously calculates a **Panic Score** (Defensive) and a **Bull Score** (Offensive) using 11 weighted indicators.
2.  **Priority Gating**: The Panic Brain always has absolute priority—if a circuit breaker is triggered, offensive signals are completely ignored.
3.  **Hysteresis Locking**: Once a switch occurs, the `lock_days` parameter enforces a mandatory holding period to prevent "flip-flopping" on market noise.
4.  **Threshold Optimization**: Evolution finds the exact sensitivity (Thresholds) for each brain to maximize capture and minimize drawdown.

---

## ⚡ QUICK LAUNCH: V3 Precision Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v3_precision --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v3_precision --pop 100 --gen 50 --vault champions/v3_precision/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v3_precision/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v3_precision/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v3_precision/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate. |
| `--vault` | `None` | Path to load seeds from. |
| `--min-cagr` | `35.0` | Minimum CAGR threshold for saving results. |
| `--ablation` | `False` | Enable "Indicator Ablation" (allows GA to disable weak indicators). |

---

## 🛡️ Best Used For
The "Aggression Benchmark." V3 is designed for traders who want to capture the maximum upside of 3x leverage during bull runs while maintaining a hair-trigger exit to CASH during volatility spikes. It is the purest expression of binary switching.
