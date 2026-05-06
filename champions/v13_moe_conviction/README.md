# 🏛️ V13.10 MOE "Conviction Aggressive"

The **V13.10 Conviction Aggressive** variant is a high-conviction evolution of the Mixture of Experts (MOE) architecture. It is specifically designed to eliminate "Conflict Drag" in 3x leveraged strategies by aggressively rewarding the winning regime.

---

## 🧬 Tactical Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Evolution** | `python tests/run_evolution_universal.py --version v13_moe_conviction --pop 100 --gen 100` |
| **Seeded Run** | `python tests/run_evolution_universal.py --version v13_moe_conviction --pop 500 --gen 100 --vault champions/v13_moe_conviction/vault` |
| **Param Optimization** | `python tests/optimize_v13_conviction.py` |

### 🔬 Diagnostics
| Goal | Command |
| :--- | :--- |
| **Full Audit** | `python tests/performance_audit.py champions/v13_moe_conviction/genome.json` |
| **X-Ray Analysis** | `python tests/genome_xray.py champions/v13_moe_conviction/genome.json` |
| **Vault Sweep** | `python tests/vault_sweep.py --vault champions/v13_moe_conviction/vault --promote --top 20` |

---

## 🧠 Conviction Architecture (v13.10)

V13.10 adds a non-linear decision layer between the Sentinel and the final allocation:

### 1. Power Skewing (`skew_power`)
The raw probabilities from the Sentinel are raised to a power (typically 2.0 - 3.5). This pushes moderate leads into dominant positions.
*   *Example*: A 60/40 split with `skew_power: 2.0` becomes a **69/31** split. A 70/30 split becomes **84/16**.

### 2. The Kill Switch (`conviction_cap`)
If the sharpened conviction exceeds a specific threshold (e.g., 90%), the strategy immediately rounds to **100% conviction**. 
*   *Benefit*: Completely eliminates the "frictional drag" of holding defensive assets when the Bull signal is overwhelming.

### 3. Hierarchical Specialists
*   **Sentinel**: Detects environment (18 features + 10 memory slots).
*   **Bear Commander**: Specialist brain for rotation (CASH, GOLD, TLT).
*   **Bull Authority**: Hardcoded to 100% 3xSPY (UPRO) when Bull regime is active.

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `skew_power` | `2.0` | Strength of the non-linear probability tilt. |
| `conviction_cap` | `0.90` | Threshold for 100% winner-take-all switch. |
| `smoothing` | `0.3` | Speed of regime transition (0.1 = stable, 0.5 = fast). |
| `temp` | `1.0` | Neural sharpening (lower = more decisive). |
