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
            position: relative;
            z-index: 1; /* Lower than table tooltips */
        }

        section { margin-bottom: 60px; position: relative; z-index: 5; }
        section h2 { font-family: 'Outfit', sans-serif; margin-bottom: 20px; font-size: 1.5rem; display: flex; align-items: center; gap: 10px; }

        table {
            width: 100%;
            border-collapse: collapse;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            /* overflow: hidden; Removed to prevent tooltip clipping */
            position: relative;
            z-index: 10;
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
            background: #111827;
            color: #fff;
            padding: 12px;
            border-radius: 10px;
            font-size: 13px;
            width: 280px;
            white-space: pre-wrap;
            z-index: 9999; /* Ensure it is above EVERYTHING */
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 20px 40px rgba(0,0,0,0.8), 0 0 20px var(--accent-glow);
            margin-bottom: 12px;
            text-transform: none;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            letter-spacing: 0;
            pointer-events: none;
            line-height: 1.6;
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
                        <th onclick="sortTable('mainTable', 4)">Calmar</th>
                        <th onclick="sortTable('mainTable', 5)">PF</th>
                        <th onclick="sortTable('mainTable', 6)">Win%</th>
                        <th onclick="sortTable('mainTable', 7)">Volat.</th>
                        <th onclick="sortTable('mainTable', 8)">Lev.</th>
                        <th onclick="sortTable('mainTable', 9)">Trades/Yr</th>
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

        <section class="methodology">
            <h2>Audit Methodology & Methodics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Execution Engine</div>
                    <div class="stat-sub" style="color: var(--text)">
                        Signals are generated using <b>Day T</b> closing data. Execution occurs on <b>Day T+1</b> using the <b>Mid-Price</b> (Average of Open and Close). Friction of <b>5 bps slippage</b> + <b>1 bps commission</b> is applied to total turnover on every rebalance.
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Institutional Costs</div>
                    <div class="stat-sub" style="color: var(--text)">
                        Daily expense ratios are deducted: <b>0.03%</b> for SPY, <b>0.91%</b> for 2x/3x ETFs. <b>CASH</b> holdings earn a conservative <b>3.5%</b> annualized yield. Leverage costs are embedded in the ETF drag.
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Resilience Protocol</div>
                    <div class="stat-sub" style="color: var(--text)">
                        Runs 50 iterations per strategy across <b>random 10-year windows</b>. This identifies strategies that only performed well due to specific starting dates (e.g., starting exactly at a market bottom).
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Synthetic Protocol</div>
                    <div class="stat-sub" style="color: var(--text)">
                        Uses <b>Block Bootstrapping</b> (21-day chunks) to create 50 "Parallel Universes." This tests if a strategy's edge is structural or if it relied on the specific sequence of historical events.
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <div class="stat-label" style="margin-bottom: 15px;">Audit Parameters (Institutional Friction)</div>
                <table style="font-size: 0.85rem; border: none; background: none;">
                    <thead>
                        <tr style="background: none; border-bottom: 1px solid var(--border);">
                            <th style="padding: 8px; border: none;">Parameter</th>
                            <th style="padding: 8px; border: none;">Value</th>
                            <th style="padding: 8px; border: none;">Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>Slippage</td><td style="color: var(--danger)">0.05% (5 bps)</td><td>Applied to total turnover volume per trade.</td></tr>
                        <tr><td>Commission</td><td style="color: var(--danger)">0.01% (1 bps)</td><td>Platform/Brokerage execution fee per trade.</td></tr>
                        <tr><td>SPY Expense</td><td style="color: var(--danger)">0.03% Annual</td><td>Standard management fee for 1x exposure.</td></tr>
                        <tr><td>UPRO/SSO Expense</td><td style="color: var(--danger)">0.91% Annual</td><td>Standard management fee for 2x/3x leverage.</td></tr>
                        <tr><td>Cash Yield</td><td style="color: var(--success)">3.50% Annual</td><td>Risk-free rate earned on idle capital.</td></tr>
                        <tr><td>Leverage Cost</td><td style="color: var(--text-dim)">Variable</td><td>Embedded in daily ETF tracking error.</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="chart-container">
                <div class="stat-label" style="margin-bottom: 15px;">Metric Definitions</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; font-size: 0.9rem;">
                    <div>
                        <p><b>CAGR:</b> Compound Annual Growth Rate. The geometric mean return that provides the same total return if the strategy had grown at a steady rate.</p>
                        <p style="margin-top:10px"><b>Sharpe Ratio:</b> Risk-adjusted return. Measures excess return per unit of volatility. Above 1.0 is considered "Good", above 2.0 is "Elite".</p>
                        <p style="margin-top:10px"><b>Profit Factor:</b> The ratio of Gross Profits to Gross Losses. A value of 1.5+ indicates a strong structural edge.</p>
                    </div>
                    <div>
                        <p><b>Max Drawdown:</b> The peak-to-trough decline during a specific period. Measures the "Maximum Pain" a trader must endure.</p>
                        <p style="margin-top:10px"><b>Calmar Ratio:</b> CAGR divided by Max Drawdown. Focuses on the trade-off between absolute return and absolute risk.</p>
                        <p style="margin-top:10px"><b>Stability/Robustness:</b> The percentage of the historical CAGR that was maintained during the Audit stress tests.</p>
                    </div>
                </div>
            </div>
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
                
                // Tooltip text for residency
                const resTooltip = `Asset Residency DNA:&#10;------------------&#10;3x SPY:  ${(a['3xSPY']*100).toFixed(1)}%&#10;2x SPY:  ${(a['2xSPY']*100).toFixed(1)}%&#10;1x SPY:  ${(a['SPY']*100).toFixed(1)}%&#10;CASH:    ${(a['CASH']*100).toFixed(1)}%`;
                
                return `<tr>
                    <td class="strat-name">${item.name}</td>
                    <td class="${m.cagr > 0 ? 'positive' : 'negative'}">${(m.cagr * 100).toFixed(2)}%</td>
                    <td class="negative">${(m.max_dd * 100).toFixed(1)}%</td>
                    <td>${m.sharpe.toFixed(2)}</td>
                    <td>${m.calmar.toFixed(2)}</td>
                    <td class="${m.profit_factor > 1.5 ? 'positive' : ''}">${m.profit_factor.toFixed(2)}</td>
                    <td>${(m.win_rate * 100).toFixed(1)}%</td>
                    <td>${(m.volatility * 100).toFixed(1)}%</td>
                    <td>${m.avg_leverage.toFixed(2)}x</td>
                    <td>${(m.num_rebalances / (item.curve.dates.length / 252)).toFixed(1)}</td>
                    <td>
                        <div class="info-icon" data-tooltip="${resTooltip}" style="background:none; width:auto; height:auto; display:inline-block; border-radius:0;">
                            <div class="residency-bar" style="width: 140px; height: 12px; border-radius: 6px; cursor: pointer; border: 0.5px solid rgba(255,255,255,0.1); display: flex; overflow: hidden;">
                                <div class="res-upro" title="3x SPY: ${(a['3xSPY']*100).toFixed(1)}%" style="width: ${a['3xSPY']*100}%"></div>
                                <div class="res-sso" title="2x SPY: ${(a['2xSPY']*100).toFixed(1)}%" style="width: ${a['2xSPY']*100}%"></div>
                                <div class="res-spy" title="1x SPY: ${(a['SPY']*100).toFixed(1)}%" style="width: ${a['SPY']*100}%"></div>
                                <div class="res-cash" title="CASH: ${(a['CASH']*100).toFixed(1)}%" style="width: ${a['CASH']*100}%"></div>
                            </div>
                        </div>
                    </td>
                </tr>`;
            }).join('');
        }

        function buildAuditTable(tableId, items, auditKey) {
            document.getElementById(tableId).innerHTML = items.map(item => {
                const a = item[auditKey];
                if (!a) return `<tr><td class="strat-name">${item.name}</td><td colspan="7" style="text-align:center; color:var(--text-dim)">Audit Pending</td></tr>`;
                
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
                    const keys = ['name', 'metrics.cagr', 'metrics.max_dd', 'metrics.sharpe', 'metrics.calmar', 'metrics.profit_factor', 'metrics.win_rate', 'metrics.volatility', 'metrics.avg_leverage', 'metrics.num_rebalances'];
                    valA = keys[colIdx].split('.').reduce((o, i) => o[i], a);
                    valB = keys[colIdx].split('.').reduce((o, i) => o[i], b);
                } else {
                    const keys = ['name', 'avg_cagr', 'med_cagr', 'avg_dd', 'med_dd', 'avg_sharpe', 'avg_trades', 'stability'];
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
