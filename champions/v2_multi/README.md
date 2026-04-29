# V2 Multi — Multi-Leverage AI

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py "Champion V1 (Manual)"

# Behavioral X-Ray (Logic DNA)
python tests/genome_xray.py "Champion V1 (Manual)"
```

## 🧠 Strategy Logic
V2 was the first version to explore **Multi-Asset Leverage**. It uses four distinct "Brain states" to select between discrete leverage levels.

### ⚙️ Decision Engine
- **4-Regime Selection**: Panic, 1x, 2x, and 3x brains.
- **Winner-Takes-All**: The brain with the highest score relative to its threshold dictates the portfolio.

### 📈 Leverage States
- **CASH / 1x / 2x / 3x**

## 🚀 Execution Commands

### 📊 Audit & Behavioral Analysis
```bash
# Institutional Performance Report
python tests/performance_audit.py champions/v2_multi/genome.json

# Behavioral X-Ray (Allocation DNA)
python tests/genome_xray.py champions/v2_multi/genome.json
```

### 🌪️ Stress Testing
```bash
# Cross-Regime Sweep (Rolling 5yr Windows). Use --promote to update champion.
python tests/vault_sweep.py --vault champions/v2_multi/vault --promote
```
