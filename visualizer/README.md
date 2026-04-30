# 🛰️ Tactical Forge Command Center (Vite Prototype)

Institutional-grade quantitative visualizer for the Tactical Forge trading ecosystem. This dashboard provides high-fidelity performance audits, robustness testing, and deep-regime strategy inspection.

## 🏗️ Architecture
- **Framework:** React 18 + Vite
- **Styling:** Tailwind CSS v4 (Modern Fluid Design)
- **Charts:** Recharts (High-performance multi-series)
- **Animation:** Framer Motion (Micro-interactions)
- **Data Engine:** Asynchronous JSON Pipeline (Public API compatible)

## 📊 Core Features
- **Institutional Audit Wall:** 16 quantitative gauges with smart-flipping interactive tooltips.
- **Cross-Regime Robustness:** Detailed Monte Carlo resilience and block-bootstrap synthetic universe reports.
- **Relative Benchmarking:** Automated SPY baseline integration for Alpha/Beta discovery.
- **Neural DNA Analysis:** (Pipeline Pending) Indicator weighting and activation heatmaps.

## 🚀 Getting Started

### 1. Installation
```bash
npm install
```

### 2. Local Development
```bash
npm run dev
```

### 3. Updating Data
The dashboard reads from `public/data.json`. To refresh this with the latest tournament results, run the exporter from the root directory:
```bash
python src/tournament/runner.py
```

## 🌐 Deployment (GitHub Pages)
The project is pre-configured for GitHub Pages under the `/trading-bot/` subpath. 

1. Build the production assets:
   ```bash
   npm run build
   ```
2. Deploy the `dist/` folder to your `gh-pages` branch.

---
**Institutional Standard | Tactical Forge Ecosystem**
