# V6 Balancer — The Multi-Brain Ensemble

## 🧠 Strategy Logic
V6 Balancer is the first architecture to use a **Softmax Ensemble** approach. Instead of binary switches, it runs four independent "Expert Brains" (Cash, 1x, 2x, 3x) and uses a temperature-scaled probability distribution to determine the final portfolio allocation.

### 🔬 Decision Engine Anatomy
1.  **Expert Brain Ensemble**: Four distinct scoring engines evolve specialized weights for their respective leverage targets.
2.  **Softmax Allocation**: Concordance across brains is resolved using a Softmax layer, allowing for smooth transitions (e.g., 50% SPY / 50% 3xSPY).
3.  **Temperature Control**: Evolution optimizes a `temp` parameter that controls how "aggressive" or "cautious" the brain consensus should be.
4.  **Ablative Lookbacks**: Every indicator in every brain has an independent, evolved lookback period with dynamic ablation support.

---

## ⚡ QUICK LAUNCH: V6 Balancer Command Center

### 🧬 Evolution (Training)
| Goal | Command |
| :--- | :--- |
| **New Run** | `python tests/run_evolution_universal.py --version v6_balancer --pop 100 --gen 100` |
| **Seed Run** | `python tests/run_evolution_universal.py --version v6_balancer --pop 100 --gen 100 --vault champions/v6_balancer/vault --mut 0.4` |

### 🔬 Diagnostics (Audit)
| Goal | Command |
| :--- | :--- |
| **Audit** | `python tests/performance_audit.py champions/v6_balancer/genome.json` |
| **X-Ray** | `python tests/genome_xray.py champions/v6_balancer/genome.json` |
| **Sweep** | `python tests/vault_sweep.py --vault champions/v6_balancer/vault --promote --top 20` |

---

## ⚙️ Evolution Parameters
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--pop` | `100` | Population size. |
| `--gen` | `50` | Number of generations. |
| `--mut` | `0.20` | Mutation rate. |
| `--vault` | `None` | Path to load seeds from. |
| `--min-cagr` | `25.0` | Minimum CAGR threshold for saving results. |
| `--no-ablation`| `True` | Disable indicator ablation (forces all indicators to stay active). |

---

## 🛡️ Best Used For
The "Smooth Operator." V6 is best for traders who dislike the volatility of binary switching and prefer a model that can "ease in" to positions as market conviction builds across multiple indicators.
