# 🏛️ Genome V13 MOE Light: Sparse Expert
Genome V13 MOE Light is a refined version of the MOE Pro architecture. It focuses on **Generalization** and **Robustness** by reducing the parameter space and forcing expert specialization.

---

## 🧬 Tactical Command Center
### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Evolution** | `python tests/run_evolution_universal.py --version v13_moe_light --pop 100 --gen 100` |
| **Seeded Run** | `python tests/run_evolution_universal.py --version v13_moe_light --pop 500 --gen 50 --vault champions/v13_moe_light/vault` |

### 🔬 Diagnostics
| Goal | Command |
| :--- | :--- |
| **Full Audit** | `python tests/performance_audit.py champions/v13_moe_light/genome.json` |
| **X-Ray Analysis** | `python tests/genome_xray.py champions/v13_moe_light/genome.json` |
| **Vault Sweep** | `python tests/vault_sweep.py --vault champions/v13_moe_light/vault --promote --top 20` |

---

## 🧠 Refined Architecture (13.6)

### 1. Sentinel (The Decider)
*   **Inputs**: All 18 macro and technical features.
*   **Role**: Determines the high-level regime probability.
*   **Change**: Removed the "Conviction Cliff" (80/60 thresholds). This version uses **100% Fluid Blending** at all times.

### 2. Bull Expert (Momentum)
*   **Inputs**: Restricted to 10 Technical/Momentum features.
*   **Role**: Optimizes leverage during confirmed uptrends.

### 3. Bear Expert (Safety)
*   **Inputs**: Restricted to 10 Macro/Volatility/Seasonality features.
*   **Role**: Manages hedges during downturns and choppy markets.

---

## 🌊 Why "Light"?
1.  **Feature Pruning**: Experts only see what they need. This prevents the experts from learning noise (overfitting).
2.  **Smaller Hidden Layer**: Reduced from 10 to 6 nodes. This significantly reduces the total parameter count, making it harder to "memorize" the backtest.
3.  **No Thresholds**: Prevents the catastrophic "all-in" failure mode during sudden reversals.
