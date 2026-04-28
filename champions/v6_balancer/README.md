# V6 Balancer — The Probabilistic Allocator

## 🧠 Strategy Logic
V6 moves beyond binary thresholds to a **Continuous Probability Model**. It treats the market as a distribution of states rather than a single fixed state.

### ⚙️ Decision Engine
- **4-Way Softmax**: Uses four independent "Brains" (Cash, 1x, 2x, 3x) that compete for allocation.
- **Weighted Consensus**: The final portfolio is the "Expected Value" of all brain confidences. 
- **Evolutionary Temperature**: Evolves a `temp` parameter to control how "aggressive" vs "smooth" the transitions are.

### 📈 Leverage States (Dynamic)
V6 can hold **Fractional Positions**:
- e.g., 20% Cash, 50% 1x SPY, 30% 2x SPY.

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v6_balancer/genome.json

# Behavioral X-Ray (Allocation DNA)
python tests/genome_xray.py champions/v6_balancer/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows)
python tests/vault_sweep.py --vault champions/v6_balancer/vault
```

### 🧬 Evolution
```bash
# Cold Start Evolution
python tests/run_evolution_v6_balancer.py --pop 500 --gen 100

# Seeded Evolution (Refine Champions)
python tests/run_evolution_v6_balancer.py --pop 300 --gen 50 --seed champions/v6_balancer/vault

### 🧪 Special Modifiers
- `--mutation 0.4`: Increase "Creative" mutation for exploration.
- `--mutation 0.1`: Decrease mutation for fine-tuning a champion.
- `--ablation`: Enable **Ablation Mode**. Allows the AI to evolve "False" states for indicators, effectively pruning its own logic tree for better generalization.
```
