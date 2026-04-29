# V6 Balancer — Probabilistic Allocator

## 🧠 Strategy Logic
V6 Balancer represents the transition from "Binary Switching" to **Probabilistic Allocation**. It treats market exposure as a continuous probability distribution, allowing for smooth gradients between risk-on and risk-off states.

### ⚙️ Softmax Engine
- **Quad-Brain Voting**: Simultaneously evaluates four independent brains: `Cash`, `1x`, `2x`, and `3x`.
- **Confidence Scaling**: Scores are passed through a Softmax function to determine the percentage allocation for each tier.
*Example: If the Panic score is high, it might allocate 80% CASH and 20% 1x SPY, adding defensive buffer without fully exiting.*

### 📊 Intelligence Layer
- **Shared Perception**: All brains look through the same "eyes" via evolved **Shared Lookbacks**.
- **Volume & Momentum Sensors**: Utilizes **MFI** (Money Flow Index) and **BBW** (Bollinger Band Width) to detect explosive accumulation.
- **Slippage Protection**: Implements a **5% Rebalance Threshold** and **Temporal Lock** to prevent over-trading.

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v6_balancer/genome.json

# Behavioral X-Ray (Allocation DNA & Transition Matrix)
python tests/genome_xray.py champions/v6_balancer/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). Use --promote to update champion.
python tests/vault_sweep.py --vault champions/v6_balancer/vault --promote
```

### 🧬 Evolution
```bash
# Seeded Evolution (Institutional Refinement)
python tests/run_evolution_v6_balancer.py --pop 500 --gen 100 --seed champions/v6_balancer/vault

# Cold Start Exploration
python tests/run_evolution_v6_balancer.py --pop 500 --gen 100 --min-cagr 0.35
```

### 🧪 Special Modifiers
- `--mutation 0.4`: Increase "Creative" mutation for exploration.
- `--mutation 0.1`: Decrease mutation for fine-tuning a champion.
- `--min-cagr 0.30`: **Performance Floor**. Ruthlessly prune underperformers.
- `--ablation`: Enable **Ablation Mode**. Allows the AI to evolve "False" states for indicators, effectively pruning its own logic tree for better generalization.
