# V4.1 Chameleon — Hybrid Hunter Engine

## 🧠 Strategy Logic (V4.1 Overhaul)
V4 Chameleon is a **Dual-Path Adaptive Engine** designed for institutional-grade performance, it actively "Hunts" for profit in bull markets while maintaining a "Fast-Exit" trigger for sudden trend breaks.

### ⚙️ Decision Engine
- **Fast-Exit (Momentum Slope)**: Monitors the short-term linear regression slope. If the trend breaks, the bot pulls to **CASH** instantly, often *before* volatility spikes.
- **Aggressive Dip-Hunting**: In Bull regimes (Price > SMA200), the bot uses **RSI Mean Reversion** to load into 3x leverage on dips and trim back to 1x when overbought.
- **Nitro Matrix Mode**: Powered by a precalculated indicator matrix (SMA, VIX, RSI, Slope) for 10x faster evolutionary simulations.
- **Staged Evaluation**: Uses a 1,000-day "Lite Screen" before full 30-year auditing to accelerate discovery.

### 📈 Leverage States
- **CASH / 1x / 2x / 3x** (Dynamic allocation based on Bull/Bear regimes)

---

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v4_chameleon/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). 
# --promote: Update main genome.json with the best performer.
python tests/vault_sweep.py --vault champions/v4_chameleon/vault --promote --top 20
```

### 🧬 Evolution
Optimizes the adaptive logic tree using **Nitro-Accelerated Gaussian Neuroevolution**.
```bash
# Standard High-Population Run
python tests/run_evolution_v4_chameleon.py --pop 3000 --gen 100 --mut 0.25 --ablation

# Seeded Evolution (Refine using your best vaulted genomes)
python tests/run_evolution_v4_chameleon.py --pop 3000 --gen 100 --seed champions/v4_chameleon/vault
```

#### ⚙️ Evolution Parameters
| Flag | Default | Description |
|------|---------|-------------|
| `--pop` | 40 | Population size. Recommend `1000+` for Nitro runs. |
| `--gen` | 15 | Number of generations. |
| `--mut` | 0.20 | Mutation rate (DNA change probability). |
| `--seed`| `None` | Path to vault dir to seed population. |
| `--ablation` | `Off` | **Feature Selection**: Dynamically prunes weak signals (VIX, MOM, RSI, SLOPE). |
| `--min-cagr` | `20.0` | Minimum CAGR % threshold for saving to the vault. |
