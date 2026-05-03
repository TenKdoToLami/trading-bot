# V5 Sniper — The Volatility Regime Hunter

## 🧠 Strategy Logic
V5 Sniper is a specialized evolution of the Precision series, designed to target specific **Volatility Thresholds**. It introduces the "Regime Corridor," where the strategy remains aggressive as long as volatility stays within an evolved "sweet spot" and retreats instantly when thresholds are breached.

### 🔬 Decision Engine Anatomy
1.  **Regime Corridor**: Evolution identifies two critical VIX thresholds (Low and High) that define the "Sniper Zone."
2.  **Ablative Indicator Weighting**: Uses 11 weighted indicators with active ablation, allowing the GA to simplify the decision logic for maximum robustness.
3.  **Adaptive Lookbacks**: Every indicator's lookback period is evolved independently, ensuring the model reacts at the optimal speed for current market cycles.
4.  **Sticky Rebalancing**: Enforces a mandatory holding period (`lock_days`) to filter out whipsaws and reduce turnover costs.

---

## ⚡ QUICK LAUNCH: V5 Sniper Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v5_sniper --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v5_sniper --pop 100 --gen 100 --vault champions/v5_sniper/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v5_sniper/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v5_sniper/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v5_sniper/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate. |
| `--vault` | `None` | Path to load seeds from. |
| `--min-cagr` | `30.0` | Minimum CAGR threshold for saving results. |
| `--no-ablation`| `True` | Disable indicator ablation (forces all indicators to stay active). |

---

## 🛡️ Best Used For
The "Volatility Specialist." V5 Sniper excels in environments where volatility is trending or mean-reverting. It is less about broad market trends and more about identifying specific risk regimes that are safe for 3x leverage.
