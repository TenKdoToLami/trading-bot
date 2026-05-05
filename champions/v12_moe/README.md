# V12 MOE — Mixture of Experts (Fluid Hierarchy)

## 🧠 Strategy Logic
V12 SMT represents the pinnacle of the Forge architecture. It uses a **Hierarchical Mixture of Experts (MoE)** structure with three specialized neural brains. By decoupling the "Regime Selection" from "Asset Allocation," it achieves professional-grade risk management and smooth portfolio transitions.

### 🔬 Mixture of Experts Anatomy
1.  **Regime Gatekeeper (Brain 1)**: A dedicated 18-input brain that predicts the probability of a Bull vs. Bear market. It uses higher hysteresis to avoid over-trading in choppy markets.
2.  **Bullish Specialist (Brain 2)**: Only active when the market is stable or euphoric. Optimized to find the alpha-peak between 1x, 2x, and 3x SPY leverage.
3.  **Defensive Specialist (Brain 3)**: Activates during institutional stress. It manages a diverse defensive pool including **Gold**, **Long-Term Treasuries (TLT)**, **Short-Term Treasuries (SHY)**, and **2x Short SPY**.
4.  **Fluid Blending**: Unlike previous versions that "flip a switch," V12 blends the Bull and Bear outputs proportionally to the Regime score, resulting in a much smoother equity curve.

---

## ⚡ QUICK LAUNCH: V12 SMT Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v12_moe --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v12_moe --pop 100 --gen 100 --vault champions/v12_moe/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v12_moe/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v12_moe/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v12_moe/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Recommended 100+ due to the high-parameter hierarchical space. |
| `--gen` | `100` | Hierarchical models take longer to converge (MoE complexity). |
| `--mut` | `0.20` | Standard mutation rate for neural weights. |

---

## 🛡️ Best Used For
The "Total Wealth Manager." V12 MOE is designed to be the only strategy you ever need. It is built to survive major depressions (using Gold and 2x Short) while outperforming in bull markets. It is the most robust model for large-scale portfolios where drawdowns must be minimized at all costs.
