# 🏛️ V13.11 MOE "Adaptive VIX"

The **V13.11 Adaptive VIX** variant is the ultimate evolution of the Mixture of Experts architecture. It combines the aggressive conviction of v13.10 with the intelligent safeguarding of the original MOE.

---

## 🧬 Tactical Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Evolution** | `python tests/run_evolution_universal.py --version v13_moe_vix --pop 100 --gen 100` |
| **Seeded Run** | `python tests/run_evolution_universal.py --version v13_moe_vix --pop 500 --gen 100 --vault champions/v13_moe_vix/vault` |
| **Param Optimization** | `python tests/optimize_v13_vix.py` |

### 🔬 Diagnostics
| Goal | Command |
| :--- | :--- |
| **Full Audit** | `python tests/performance_audit.py champions/v13_moe_vix/genome.json` |
| **X-Ray Analysis** | `python tests/genome_xray.py champions/v13_moe_vix/genome.json` |
| **Vault Sweep** | `python tests/vault_sweep.py --vault champions/v13_moe_vix/vault --promote --top 20` |

---

## 🧠 Adaptive Conviction (v13.11)

V13.11 makes the decision-making engine "aware" of market fear (VIX):

### 1. Dynamic Kill Switch (`vix_base_cap` + `vix_sensitivity`)
The threshold for "Full Power" is no longer static. It shifts based on the VIX:
*   **Low VIX (Calm)**: The threshold drops. If the bot is even slightly bullish, it goes **100% Long** to maximize CAGR.
*   **High VIX (Storm)**: The threshold rises. This forces the bot to stay in **"Split Mode"** (Safeguards), allowing it to hedge with Gold/Cash/TLT during high-risk periods.

### 2. The Logic Matrix:
*   **VIX < 18**: Pure Aggression Mode (Maximize 3x Gains).
*   **VIX 18 - 25**: Transition Zone (Gradual shift to safety).
*   **VIX > 28**: Safeguard Mode (Preserve Capital using splits).

---

## ⚙️ Key Evolution Parameters
| Flag | Description |
| :--- | :--- |
| `vix_base_cap` | The minimum conviction required to snap to 100% in a calm market. |
| `vix_sensitivity` | How much "extra conviction" is required for every 1 point increase in VIX. |
| `skew_power` | The strength of the non-linear signal sharpening. |
