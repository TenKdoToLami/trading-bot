# V5 Sniper — Tiered Entry Specialist

## 🧠 Strategy Logic
V5 Sniper is designed to be **Always Invested**. It removes the "Cash" state entirely to avoid the risk of being out of the market during sudden rallies. Instead, it uses **Tiered Leverage** to scale conviction.

### ⚙️ Decision Engine
- **State Hunter**: Evaluates a single "Sniper Brain" to determine the conviction level.
- **Dynamic Thresholds**: Evolves two thresholds (`t_low` and `t_high`) to define the boundaries between tiers.

### 📈 Leverage States
- **1x SPY (Baseline)**: The default state when the brain is unconvicted or cautious.
- **2x SPY (Moderate Conviction)**: Triggered when the brain score crosses `t_low`.
- **3x SPY (High Conviction)**: Triggered when the brain score crosses `t_high`.

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v5_sniper/genome.json

# Behavioral X-Ray (Allocation DNA)
python tests/genome_xray.py champions/v5_sniper/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows)
python tests/vault_sweep.py --vault champions/v5_sniper/vault
```

### 🧬 Evolution
```bash
# Cold Start Evolution
python tests/run_evolution_v5_sniper.py --pop 300 --gen 100

# Seeded Evolution (Refine Champions)
python tests/run_evolution_v5_sniper.py --pop 300 --gen 50 --seed champions/v5_sniper/vault

### 🧪 Special Modifiers
- `--mutation 0.4`: Increase "Creative" mutation for exploration.
- `--mutation 0.1`: Decrease mutation for fine-tuning a champion.
- `--ablation`: Enable **Ablation Mode**. Allows the AI to evolve "False" states for indicators, effectively pruning its own logic tree for better generalization.
```
