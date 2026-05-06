# 🏛️ Genome V13 MOE Pro: Fluid Command
Genome V13 MOE (Mixture of Experts) Pro is an institutional-grade tactical allocator. It utilizes a **Triple-Brain architecture** to manage regime detection, leveraged offensive playbooks, and multi-asset defensive hedges simultaneously.

---

## 🧬 Tactical Command Center
### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Evolution** | `python tests/run_evolution_universal.py --version v13_moe --pop 100 --gen 100` |
| **Seeded Run** | `python tests/run_evolution_universal.py --version v13_moe --pop 500 --gen 50 --vault champions/v13_moe/vault` |

### 🔬 Diagnostics
| Goal | Command |
| :--- | :--- |
| **Full Audit** | `python tests/performance_audit.py champions/v13_moe/genome.json` |
| **X-Ray Analysis** | `python tests/genome_xray.py champions/v13_moe/genome.json` |
| **Vault Sweep** | `python tests/vault_sweep.py --vault champions/v13_moe/vault --promote --top 20` |

---

## 🧠 Brain Structure (13.5)

### 1. The Sentinel (Regime)
*   **Thresholds**: Uses **80% Bull** and **60% Bear** conviction triggers.
*   **Role**: Determines the blend between the Offensive and Defensive baskets.

### 2. The Bull Expert (Offense)
*   **Assets**: SPY, 2x SPY (SSO), 3x SPY (UPRO).
*   **Logic**: Optimizes leverage distribution based on technical momentum.

### 3. The Bear Expert (Defense)
*   **Assets**: TLT (Long Bonds), SHY (Short Bonds), Gold, -1x SPY, -2x SPY.
*   **Logic**: Selects the highest-probability "Safe Haven" based on macro signals (VIX, Credit Spreads).

---

## 🌊 Fluid Blending
V13 MOE Pro uses **Softmax Confidence Blending**. It doesn't just switch; it "fades" between regimes.
*   **Example**: If Sentinel is 70% Bull, the portfolio might be 50% UPRO (Bull chunk) and 20% Gold (Bear chunk), creating a natural hedge during volatile transitions.
