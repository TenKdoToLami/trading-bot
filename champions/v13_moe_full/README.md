# 🏛️ Genome V13 MOE Full: The Grand Commander (Long Only)
Genome V13 MOE Full is the ultimate evolution of the MOE architecture. It utilizes a **Hierarchical Mixture of Experts (HMOE)** to manage 3 distinct brains for regime detection and tactical capital allocation.

---

## 🧬 Tactical Command Center
### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Evolution** | `python tests/run_evolution_universal.py --version v13_moe_full --pop 100 --gen 100` |
| **Seeded Run** | `python tests/run_evolution_universal.py --version v13_moe_full --pop 500 --gen 100 --vault champions/v13_moe_full/vault` |
| **Param Optimization** | `python tests/optimize_v13_optuna.py` |

### 🔬 Diagnostics
| Goal | Command |
| :--- | :--- |
| **Full Audit** | `python tests/performance_audit.py champions/v13_moe_full/genome.json` |
| **X-Ray Analysis** | `python tests/genome_xray.py champions/v13_moe_full/genome.json` |
| **Vault Sweep** | `python tests/vault_sweep.py --vault champions/v13_moe_full/vault --promote --top 20` |

---

## 🧠 Hierarchical Architecture (13.8 - Long Only)

### 1. Sentinel (The Decider)
*   **Outputs**: [Bull Authority, Bear Authority]
*   **Role**: Determines the high-level regime. If momentum is positive, it gives authority to the Bull Expert. If volatility is rising, it hands control to the Bear Commander.

### 2. Bull Expert (Offense)
*   **Outputs**: [3x SPY (UPRO), 2x SPY (SSO), 1x SPY (VOO)]
*   **Role**: Technical momentum optimization for bullish regimes.

### 3. Bear Commander (Defense)
*   **Outputs**: [CASH, GOLD, TLT]
*   **Role**: Tactical capital preservation. 

---

## 🌊 Key Features (V13.8)
1.  **Long-Only Mandate**: Completely removed inverse ETFs to eliminate volatility decay and "short squeeze" risk.
2.  **3-Brain HMOE**: Decouples "Asset Selection" from "Regime Detection," allowing experts to specialize.
3.  **Institutional Robustness**: Tuned for high-fidelity simulation with realistic slippage, commission, and a mandatory 200-day warmup for all metrics.

---

## 🔬 Advanced Optimization Pipeline

### 1. Optuna "Memory Library" System
*   **Zero-Latency Seeding**: All genomes in the `vault/` are loaded into RAM at startup. This prevents crashes and allows real-time vault cleanup while Optuna is active.
*   **Multi-Seed Library Mode**: Every trial picks a random high-performer from the vault as its starting point, enabling true population-level evolution.

### 2. Bayesian Engine (Multivariate TPE)
*   **Interaction Awareness**: Uses Optuna's `multivariate=True` sampler to identify non-linear relationships between neural gains and market indicators.
*   **High-Speed Search**: Tuned for high-concurrency (18+ workers) to maximize search throughput.

### 3. Institutional Simulation Standards
*   **200-Day Warmup**: Mandatory stabilization period before any metrics are recorded. This delivers "Honest CAGR" by removing initial indicator drag.
*   **Execution Friction**: Includes **5bps Slippage** and **1bp Commission** as standard simulation parameters.
*   **Early Exit Pruning**: Bayesian search automatically prunes strategies that breach a **55% Drawdown**, focusing only on institutional-grade resilience.