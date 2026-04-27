REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tactical Forge - Tournament Audit</title>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Outfit:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0a0b10;
            --card-bg: rgba(255, 255, 255, 0.03);
            --border: rgba(255, 255, 255, 0.08);
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.3);
            --text: #e2e8f0;
            --text-dim: #94a3b8;
            --success: #10b981;
            --danger: #ef4444;
            --info: #3b82f6;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background-color: var(--bg); 
            color: var(--text); 
            font-family: 'Inter', sans-serif;
            line-height: 1.5;
            overflow-x: hidden;
        }

        .container { max-width: 1400px; margin: 0 auto; padding: 40px 20px; }

        header { margin-bottom: 40px; display: flex; justify-content: space-between; align-items: flex-end; }
        h1 { font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 2.5rem; letter-spacing: -1px; }
        .meta { color: var(--text-dim); font-size: 0.9rem; }

        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 40px; 
        }

        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            padding: 24px;
            border-radius: 16px;
            backdrop-filter: blur(10px);
        }
        .stat-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-dim); margin-bottom: 8px; }
        .stat-value { font-size: 1.8rem; font-weight: 700; font-family: 'Outfit', sans-serif; }
        .stat-sub { font-size: 0.85rem; color: var(--text-dim); margin-top: 4px; }

        .chart-container {
            background: var(--card-bg);
            border: 1px solid var(--border);
            padding: 24px;
            border-radius: 20px;
            margin-bottom: 40px;
        }

        section { margin-bottom: 60px; }
        section h2 { font-family: 'Outfit', sans-serif; margin-bottom: 20px; font-size: 1.5rem; display: flex; align-items: center; gap: 10px; }

        table {
            width: 100%;
            border-collapse: collapse;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
        }
        th, td { padding: 14px 16px; text-align: left; border-bottom: 1px solid var(--border); }
        th { 
            background: rgba(255,255,255,0.05); 
            font-size: 0.7rem; 
            text-transform: uppercase; 
            letter-spacing: 1px; 
            color: var(--text-dim);
            cursor: pointer;
            transition: background 0.2s;
            white-space: nowrap;
        }
        th:hover { background: rgba(255,255,255,0.1); }
        
        tr:hover td { background: rgba(255,255,255,0.02); }
        .strat-name { font-weight: 600; color: #fff; }
        .positive { color: var(--success); }
        .negative { color: var(--danger); }

        .residency-bar {
            height: 8px;
            width: 120px;
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
            display: inline-flex;
            overflow: hidden;
            vertical-align: middle;
        }
        .res-upro { background: #ef4444; height: 100%; }
        .res-sso { background: #f59e0b; height: 100%; }
        .res-spy { background: #3b82f6; height: 100%; }
        .res-cash { background: #64748b; height: 100%; }

        /* Tooltip */
        .info-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 16px;
            height: 16px;
            background: var(--info);
            color: white;
            border-radius: 50%;
            font-size: 10px;
            font-weight: 800;
            font-style: normal;
            cursor: help;
            position: relative;
        }
        .info-icon:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #1e293b;
            color: #fff;
            padding: 10px;
            border-radius: 8px;
            font-size: 12px;
            width: 250px;
            white-space: normal;
            z-index: 100;
            border: 1px solid var(--border);
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            margin-bottom: 10px;
            text-transform: none;
            font-family: 'Inter', sans-serif;
            font-weight: 400;
            letter-spacing: 0;
        }

        .badge {
            font-size: 0.65rem;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(255,255,255,0.1);
            color: var(--text-dim);
            font-weight: 600;
        }

        #mainChart { height: 500px; }
        
        .tab-btn {
            background: none;
            border: none;
            color: var(--text-dim);
            padding: 8px 16px;
            cursor: pointer;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            border-bottom: 2px solid transparent;
        }
        .tab-btn.active {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <div class="meta">Tactical Forge Laboratory</div>
                <h1>Market Intelligence Audit</h1>
            </div>
            <div class="meta" id="reportDate"></div>
        </header>

        <div class="stats-grid" id="statsGrid"></div>

        <section>
            <h2>Performance Discovery</h2>
            <div class="chart-container">
                <div id="mainChart"></div>
            </div>
            
            <table id="mainTable">
                <thead>
                    <tr>
                        <th onclick="sortTable('mainTable', 0)">Strategy</th>
                        <th onclick="sortTable('mainTable', 1)">CAGR</th>
                        <th onclick="sortTable('mainTable', 2)">Max DD</th>
                        <th onclick="sortTable('mainTable', 3)">Sharpe</th>
                        <th onclick="sortTable('mainTable', 4)">Volat.</th>
                        <th onclick="sortTable('mainTable', 5)">Lev.</th>
                        <th onclick="sortTable('mainTable', 6)">Trades/Yr</th>
                        <th>Residency <i class="info-icon" data-tooltip="Percentage of time spent in each leverage tier. Red: 3x, Yellow: 2x, Blue: 1x, Gray: Cash.">i</i></th>
                    </tr>
                </thead>
                <tbody id="mainTableBody"></tbody>
            </table>
        </section>

        <section>
            <h2>Resilience Audit <i class="info-icon" data-tooltip="Performance across 100 random 10-year periods. Stability measures how much of the original CAGR is maintained across different starting conditions.">i</i></h2>
            <table id="resilienceTable">
                <thead>
                    <tr>
                        <th onclick="sortTable('resilienceTable', 0)">Strategy</th>
                        <th onclick="sortTable('resilienceTable', 1)">Avg CAGR</th>
                        <th onclick="sortTable('resilienceTable', 2)">Med CAGR</th>
                        <th onclick="sortTable('resilienceTable', 3)">Avg DD</th>
                        <th onclick="sortTable('resilienceTable', 4)">Med DD</th>
                        <th onclick="sortTable('resilienceTable', 5)">Avg Sharpe</th>
                        <th onclick="sortTable('resilienceTable', 6)">Avg Trades</th>
                        <th onclick="sortTable('resilienceTable', 7)">Stability</th>
                    </tr>
                </thead>
                <tbody id="resilienceTableBody"></tbody>
            </table>
        </section>

        <section>
            <h2>Synthetic Robustness <i class="info-icon" data-tooltip="Performance across 100 synthetic parallel universes created via Block Bootstrapping. Tests if the edge is independent of historical sequencing.">i</i></h2>
            <table id="syntheticTable">
                <thead>
                    <tr>
                        <th onclick="sortTable('syntheticTable', 0)">Strategy</th>
                        <th onclick="sortTable('syntheticTable', 1)">Avg CAGR</th>
                        <th onclick="sortTable('syntheticTable', 2)">Med CAGR</th>
                        <th onclick="sortTable('syntheticTable', 3)">Avg DD</th>
                        <th onclick="sortTable('syntheticTable', 4)">Med DD</th>
                        <th onclick="sortTable('syntheticTable', 5)">Avg Sharpe</th>
                        <th onclick="sortTable('syntheticTable', 6)">Avg Trades</th>
                        <th onclick="sortTable('syntheticTable', 7)">Robustness</th>
                    </tr>
                </thead>
                <tbody id="syntheticTableBody"></tbody>
            </table>
        </section>
    </div>

    <script>
        const data = {{ DATA_JSON }};
        document.getElementById('reportDate').textContent = new Date().toLocaleString();

        const sortedByCagr = [...data].sort((a, b) => b.metrics.cagr - a.metrics.cagr);
        const bestCagr = sortedByCagr[0];
        const bestSharpe = [...data].sort((a, b) => b.metrics.sharpe - a.metrics.sharpe)[0];
        const bestDD = [...data].sort((a, b) => b.metrics.max_dd - a.metrics.max_dd)[0];

        document.getElementById('statsGrid').innerHTML = `
            <div class="stat-card"><div class="stat-label">Champion</div><div class="stat-value positive">${(bestCagr.metrics.cagr * 100).toFixed(1)}%</div><div class="stat-sub">${bestCagr.name}</div></div>
            <div class="stat-card"><div class="stat-label">Alpha Leader</div><div class="stat-value" style="color: var(--accent)">${bestSharpe.metrics.sharpe.toFixed(2)}</div><div class="stat-sub">${bestSharpe.name}</div></div>
            <div class="stat-card"><div class="stat-label">Drawdown Floor</div><div class="stat-value negative">${(bestDD.metrics.max_dd * 100).toFixed(1)}%</div><div class="stat-sub">${bestDD.name}</div></div>
            <div class="stat-card"><div class="stat-label">Universe</div><div class="stat-value">${data.length}</div><div class="stat-sub">Strategies Evaluated</div></div>
        `;

        // 2. Build Tables
        function buildMainTable(items) {
            document.getElementById('mainTableBody').innerHTML = items.map(item => {
                const m = item.metrics; const a = m.allocation_pct;
                return `<tr>
                    <td class="strat-name">${item.name}</td>
                    <td class="${m.cagr > 0 ? 'positive' : 'negative'}">${(m.cagr * 100).toFixed(2)}%</td>
                    <td class="negative">${(m.max_dd * 100).toFixed(1)}%</td>
                    <td>${m.sharpe.toFixed(2)}</td>
                    <td>${(m.volatility * 100).toFixed(1)}%</td>
                    <td>${m.avg_leverage.toFixed(2)}x</td>
                    <td>${(m.num_rebalances / (item.curve.dates.length / 252)).toFixed(1)}</td>
                    <td><div class="residency-bar">
                        <div class="res-upro" style="width: ${a['3xSPY']*100}%"></div>
                        <div class="res-sso" style="width: ${a['2xSPY']*100}%"></div>
                        <div class="res-spy" style="width: ${a['SPY']*100}%"></div>
                        <div class="res-cash" style="width: ${a['CASH']*100}%"></div>
                    </div></td>
                </tr>`;
            }).join('');
        }

        function buildAuditTable(tableId, items, auditKey) {
            document.getElementById(tableId).innerHTML = items.map(item => {
                const a = item[auditKey];
                if (!a) return `<tr><td class="strat-name">${item.name}</td><td colspan="6" style="text-align:center; color:var(--text-dim)">Audit Pending</td></tr>`;
                
                // Stability/Robustness score logic
                const baselineCagr = item.metrics.cagr * 100;
                const score = (a.avg_cagr / baselineCagr * 100).toFixed(0);
                let badgeClass = score > 80 ? 'positive' : score > 50 ? '' : 'negative';

                return `<tr>
                    <td class="strat-name">${item.name}</td>
                    <td class="${a.avg_cagr > 0 ? 'positive' : 'negative'}">${a.avg_cagr.toFixed(2)}%</td>
                    <td>${a.med_cagr.toFixed(2)}%</td>
                    <td class="negative">${a.avg_dd.toFixed(1)}%</td>
                    <td>${a.med_dd.toFixed(1)}%</td>
                    <td>${a.avg_sharpe.toFixed(2)}</td>
                    <td>${a.avg_trades.toFixed(1)}</td>
                    <td><span class="badge ${badgeClass}">${score}% Consistent</span></td>
                </tr>`;
            }).join('');
        }

        buildMainTable(sortedByCagr);
        buildAuditTable('resilienceTableBody', sortedByCagr, 'resilience');
        buildAuditTable('syntheticTableBody', sortedByCagr, 'synthetic');

        // 3. Sorting
        let sortStates = {};
        function sortTable(tableId, colIdx) {
            if (!sortStates[tableId]) sortStates[tableId] = { col: -1, dir: 1 };
            const state = sortStates[tableId];
            if (state.col === colIdx) state.dir *= -1; else state.dir = 1;
            state.col = colIdx;

            const tbodyId = tableId + 'Body';
            const auditKey = tableId === 'resilienceTable' ? 'resilience' : tableId === 'syntheticTable' ? 'synthetic' : null;
            
            const sorted = [...data].sort((a, b) => {
                let valA, valB;
                if (!auditKey) {
                    const keys = ['name', 'metrics.cagr', 'metrics.max_dd', 'metrics.sharpe', 'metrics.volatility', 'metrics.avg_leverage'];
                    valA = keys[colIdx].split('.').reduce((o, i) => o[i], a);
                    valB = keys[colIdx].split('.').reduce((o, i) => o[i], b);
                } else {
                    const keys = ['name', 'avg_cagr', 'med_cagr', 'avg_dd', 'med_dd', 'avg_sharpe', 'stability'];
                    valA = colIdx === 0 ? a.name : (a[auditKey] ? a[auditKey][keys[colIdx]] : -999);
                    valB = colIdx === 0 ? b.name : (b[auditKey] ? b[auditKey][keys[colIdx]] : -999);
                }
                if (typeof valA === 'string') return valA.localeCompare(valB) * state.dir;
                return (valA - valB) * state.dir;
            });

            if (!auditKey) buildMainTable(sorted); else buildAuditTable(tbodyId, sorted, auditKey);
        }

        // 4. Chart
        const traces = data.map(item => ({
            x: item.curve.dates, y: item.curve.equities, name: item.name,
            type: 'scatter', mode: 'lines', line: { width: 2 },
            hovertemplate: '<b>%{x}</b><br>$%{y:.2f}<extra></extra>'
        }));
        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#94a3b8', family: 'Inter' },
            xaxis: { gridcolor: 'rgba(255,255,255,0.05)', rangeselector: { buttons: [{count: 5, label: '5y', step: 'year'}, {step: 'all'}] } },
            yaxis: { type: 'log', gridcolor: 'rgba(255,255,255,0.05)', title: 'Growth of $1 (Log)' },
            legend: { orientation: 'h', y: -0.2 }, margin: { t: 20, r: 20, l: 60, b: 80 }, hovermode: 'x unified'
        };
        Plotly.newPlot('mainChart', traces, layout, { responsive: true, displaylogo: false });
    </script>
</body>
</html>
"""
