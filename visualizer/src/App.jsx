import React, { useState, useEffect, useMemo } from 'react';
import { 
  TrendingUp, Shield, Zap, BarChart3, Activity, Globe, Check, ChevronLeft,
  Plus, Bolt, LineChart as LucideLineChart, Gem, Scale, ExternalLink, Info
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, 
  Legend, AreaChart, Area, BarChart, Bar, Cell
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Internal Components
import { RiskGaugeCard } from './components/RiskGaugeCard';
import { AuditCard } from './components/AuditCard';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const COLORS = [
  "#6366f1", "#10b981", "#ef4444", "#3b82f6", "#f59e0b", "#ec4899", "#8b5cf6", "#14b8a6"
];

export default function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNames, setSelectedNames] = useState([]);
  const [inspectionStrategy, setInspectionStrategy] = useState(null);
  const [activeTab, setActiveTab] = useState('performance');
  const [scaleMode, setScaleMode] = useState('log');

  useEffect(() => {
    fetch('/trading-bot/data.json')
      .then(res => res.json())
      .then(json => {
        setData(json);
        setSelectedNames(json.slice(0, 3).map(s => s.name));
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load data:", err);
        fetch('/data.json')
          .then(res => res.json())
          .then(json => {
            setData(json);
            setSelectedNames(json.slice(0, 3).map(s => s.name));
            setLoading(false);
          });
      });
  }, []);

  const spyData = useMemo(() => data.find(s => s.name.includes('B&H SPY')), [data]);
  const bestCagr = useMemo(() => data.length ? [...data].sort((a, b) => b.metrics.cagr - a.metrics.cagr)[0] : null, [data]);

  const chartData = useMemo(() => {
    if (!data.length || !selectedNames.length) return [];
    const baseDates = data[0].curve.dates;
    return baseDates.map((date, i) => {
      const point = { date };
      selectedNames.forEach(name => {
        const strat = data.find(s => s.name === name);
        if (strat) point[name] = strat.curve.equities[i];
      });
      return point;
    });
  }, [data, selectedNames]);

  const toggleStrategy = (name) => {
    setSelectedNames(prev => prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]);
  };

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-background text-slate-200">
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }}>
          <Zap className="text-accent w-12 h-12" />
        </motion.div>
      </div>
    );
  }

  const customTooltipStyle = {
    backgroundColor: '#0f172a',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '12px',
    color: '#f8fafc',
    fontSize: '11px',
    boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)'
  };

  return (
    <div className="min-h-screen bg-background text-slate-200 flex font-sans selection:bg-accent/30">
      <aside className="w-80 border-r border-border p-6 flex flex-col gap-8 glass shrink-0 sticky top-0 h-screen">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-accent rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.4)]">
            <TrendingUp className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="font-outfit font-bold text-xl tracking-tight text-white">Tactical Forge</h1>
            <p className="text-xs text-slate-500 uppercase font-bold tracking-widest">Command Center</p>
          </div>
        </div>
        <nav className="flex flex-col gap-2">
          <button
            onClick={() => { setActiveTab('performance'); setInspectionStrategy(null); }}
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-xl transition-all",
              activeTab === 'performance' && !inspectionStrategy ? "bg-accent/10 text-accent border border-accent/20" : "hover:bg-white/5 text-slate-400"
            )}
          >
            <BarChart3 className="w-5 h-5" />
            <span className="font-semibold">Tournament Audit</span>
          </button>
        </nav>
        <div className="flex-1 flex flex-col overflow-hidden">
          <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest mb-2 px-3">Active Selection</p>
          <div className="flex-1 overflow-y-auto space-y-1 px-1 custom-scrollbar">
            {data.map(strat => (
              <button
                key={strat.name}
                onClick={() => toggleStrategy(strat.name)}
                className={cn(
                  "w-full text-left px-3 py-2 rounded-lg text-xs flex items-center justify-between transition-all",
                  selectedNames.includes(strat.name) ? "bg-white/5 text-slate-200" : "text-slate-500 hover:text-slate-300"
                )}
              >
                <div className="flex items-center gap-2 truncate">
                  <div className={cn("w-2 h-2 rounded-full", selectedNames.includes(strat.name) ? "bg-accent" : "bg-slate-700")} />
                  <span className="truncate">{strat.name}</span>
                </div>
                {selectedNames.includes(strat.name) && <Check className="w-3 h-3 text-accent shrink-0" />}
              </button>
            ))}
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-10 relative">
        <AnimatePresence mode="wait">
          {inspectionStrategy ? (
            <motion.div
              key="inspection"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-8"
            >
              <header className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <button onClick={() => setInspectionStrategy(null)} className="p-2 rounded-xl bg-white/5 border border-border hover:bg-white/10 transition-all text-white">
                    <ChevronLeft className="w-6 h-6" />
                  </button>
                  <div>
                    <h2 className="text-3xl font-outfit font-extrabold tracking-tight flex items-center gap-3 text-white">
                      {inspectionStrategy.name}
                      <span className="text-xs px-2 py-0.5 bg-accent/20 text-accent rounded-full border border-accent/20 font-bold uppercase tracking-widest">Inspection Active</span>
                    </h2>
                    <p className="text-slate-500 text-sm">Institutional Quantitative Behavioral Analysis</p>
                  </div>
                </div>
              </header>

              <div className="flex flex-wrap gap-4">
                 <RiskGaugeCard 
                    title="Total Return" 
                    value={`${inspectionStrategy.metrics.multiplier?.toFixed(1) || 'N/A'}x`} 
                    subValue="Cumulative Multiplier" 
                    colorClass="text-success"
                    tooltipProps={{
                      explanation: "The total multiplier of original capital over the entire period.",
                      goodRange: "> 50x (Strategic Lead)",
                      spyValue: `${spyData?.metrics.multiplier?.toFixed(1)}x`,
                      formula: "(Ending / Starting Value)"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Annual CAGR" 
                    value={`${(inspectionStrategy.metrics.cagr * 100).toFixed(1)}%`} 
                    subValue="Geometric Mean" 
                    colorClass="text-success"
                    tooltipProps={{
                      explanation: "Compound Annual Growth Rate. The smooth annual rate of return.",
                      goodRange: "> 15% (Institutional)",
                      spyValue: `${(spyData?.metrics.cagr * 100).toFixed(1)}%`,
                      formula: "((End / Start)^(1/Years)) - 1"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Max Drawdown" 
                    value={`${(inspectionStrategy.metrics.max_dd * 100).toFixed(1)}%`} 
                    subValue="Structural Risk" 
                    colorClass={inspectionStrategy.metrics.max_dd < -0.5 ? "text-danger" : "text-success"}
                    progress={(1 + inspectionStrategy.metrics.max_dd) * 100}
                    trackClass="bg-gradient-to-r from-danger to-success"
                    tooltipProps={{
                      explanation: "Largest peak-to-trough decline. Measures maximum pain threshold.",
                      goodRange: "> -30% (High Quality)",
                      spyValue: `${(spyData?.metrics.max_dd * 100).toFixed(1)}%`,
                      formula: "(Peak - Trough) / Peak"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Ann. Volatility" 
                    value={`${(inspectionStrategy.metrics.volatility * 100).toFixed(1)}%`} 
                    subValue="Price Fluctuations" 
                    progress={100 - (inspectionStrategy.metrics.volatility * 200)}
                    trackClass="bg-gradient-to-r from-danger to-success"
                    tooltipProps={{
                      explanation: "Standard deviation of returns. Higher volatility means more aggressive swings.",
                      goodRange: "< 25% (Controlled)",
                      spyValue: `${(spyData?.metrics.volatility * 100).toFixed(1)}%`,
                      formula: "StdDev(Daily) * sqrt(252)"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Annual Pivots" 
                    value={inspectionStrategy.metrics.trades_per_year.toFixed(1)} 
                    subValue="Yearly Rebalances" 
                    tooltipProps={{
                      explanation: "The frequency of strategy rebalancing per year. High pivots increase slippage risk.",
                      goodRange: "< 50 (Tactical)",
                      spyValue: "1.0",
                      formula: "Total Rebalances / Years"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Trades / Mo" 
                    value={(inspectionStrategy.metrics.trades_per_year / 12).toFixed(1)} 
                    subValue="Rebalance Freq" 
                    tooltipProps={{
                      explanation: "Average monthly rebalancing frequency.",
                      goodRange: "< 5.0 (Tactical)",
                      spyValue: "0.1",
                      formula: "Total Rebalances / Months"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Avg Leverage" 
                    value={`${inspectionStrategy.metrics.avg_leverage?.toFixed(2)}x`} 
                    subValue="Portfolio Heaviness" 
                    colorClass="text-info"
                    tooltipProps={{
                      explanation: "The average daily exposure multiplier. Institutional norm is 1.0x.",
                      goodRange: "1.0x - 2.0x (Prudent)",
                      spyValue: "1.00x",
                      formula: "Sum(Daily Exposure) / Days"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Expectancy" 
                    value={`${(inspectionStrategy.metrics.expectancy * 100).toFixed(2)}%`} 
                    subValue="Edge per Day" 
                    progress={inspectionStrategy.metrics.expectancy * 500}
                    trackClass="bg-gradient-to-r from-danger to-success"
                    tooltipProps={{
                      explanation: "The mathematical edge. Average expected profit per day.",
                      goodRange: "> 0.10% (Exceptional)",
                      spyValue: `${(spyData?.metrics.expectancy * 100).toFixed(2)}%`,
                      formula: "Mean(Daily Returns)"
                    }}
                 />
              </div>

              <div className="flex flex-wrap gap-4">
                 <RiskGaugeCard 
                    title="Sharpe" 
                    value={inspectionStrategy.metrics.sharpe.toFixed(2)} 
                    icon={Bolt}
                    progress={inspectionStrategy.metrics.sharpe * 33} 
                    trackClass="bg-gradient-to-r from-danger via-yellow-500 to-success"
                    tooltipProps={{
                      explanation: "Risk-adjusted return. Measures reward per unit of volatility.",
                      goodRange: "> 1.0 (Professional)",
                      spyValue: spyData?.metrics.sharpe.toFixed(2),
                      formula: "(Mean Ret - RF) / Vol"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Beta" 
                    value={inspectionStrategy.metrics.beta?.toFixed(2) || 'N/A'} 
                    icon={LucideLineChart}
                    progress={100 - (Math.abs(inspectionStrategy.metrics.beta - 1) * 50)} 
                    trackClass="bg-gradient-to-r from-danger via-success to-danger"
                    tooltipProps={{
                      explanation: "Sensitivity to market moves. 1.0 means perfectly correlated to SPY.",
                      goodRange: "0.8 - 1.2 (Neutral)",
                      spyValue: "1.00",
                      formula: "Cov(Port, Market) / Var(Market)"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Sortino" 
                    value={inspectionStrategy.metrics.sortino?.toFixed(2) || 'N/A'} 
                    icon={Shield}
                    progress={inspectionStrategy.metrics.sortino * 33} 
                    trackClass="bg-gradient-to-r from-danger via-yellow-500 to-success"
                    tooltipProps={{
                      explanation: "Adjusted return focusing only on 'bad' downside volatility.",
                      goodRange: "> 1.5 (Excellent)",
                      spyValue: spyData?.metrics.sortino?.toFixed(2),
                      formula: "(Mean Ret - RF) / DownsideVol"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Alpha" 
                    value={`${((inspectionStrategy.metrics.alpha || 0) * 100).toFixed(1)}%`} 
                    icon={Gem}
                    progress={(inspectionStrategy.metrics.alpha + 0.1) * 500} 
                    trackClass="bg-gradient-to-r from-danger to-success"
                    tooltipProps={{
                      explanation: "True skill. Performance added beyond market beta exposure.",
                      goodRange: "> 5.0% (Alpha Lead)",
                      spyValue: "0.0%",
                      formula: "Ret - (RF + Beta * (Mkt - RF))"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Information" 
                    value={inspectionStrategy.metrics.information_ratio?.toFixed(2) || 'N/A'} 
                    icon={Info}
                    progress={inspectionStrategy.metrics.information_ratio * 50} 
                    trackClass="bg-gradient-to-r from-danger to-success"
                    tooltipProps={{
                      explanation: "Measures consistency of excess returns relative to SPY.",
                      goodRange: "> 0.5 (Consistent)",
                      spyValue: "0.00",
                      formula: "(Port - Bench) / Tracking Error"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Calmar" 
                    value={inspectionStrategy.metrics.calmar?.toFixed(2) || 'N/A'} 
                    icon={TrendingUp}
                    progress={inspectionStrategy.metrics.calmar * 50} 
                    trackClass="bg-gradient-to-r from-danger to-success"
                    tooltipProps={{
                      explanation: "Return-to-Drawdown ratio. Measures pain-adjusted efficiency.",
                      goodRange: "> 0.8 (Resilient)",
                      spyValue: spyData?.metrics.calmar?.toFixed(2),
                      formula: "Annual CAGR / Max Drawdown"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Treynor Ratio" 
                    value={`${((inspectionStrategy.metrics.treynor || 0) * 100).toFixed(1)}%`} 
                    icon={ExternalLink}
                    progress={(inspectionStrategy.metrics.treynor || 0) * 500} 
                    trackClass="bg-gradient-to-r from-danger to-success"
                    tooltipProps={{
                      explanation: "Risk-adjusted return focusing on systematic (market) risk.",
                      goodRange: "> 10% (Alpha Hunter)",
                      spyValue: `${((spyData?.metrics.treynor || 0) * 100).toFixed(1)}%`,
                      formula: "(Ret - RF) / Beta"
                    }}
                 />
                 <RiskGaugeCard 
                    title="Omega Ratio" 
                    value={inspectionStrategy.metrics.omega?.toFixed(2) || 'N/A'} 
                    icon={Scale}
                    progress={(inspectionStrategy.metrics.omega || 1) * 40} 
                    trackClass="bg-gradient-to-r from-danger to-success"
                    tooltipProps={{
                      explanation: "Probability-weighted ratio of gains vs losses. Measures 'good' vs 'bad' outcomes.",
                      goodRange: "> 1.15 (Favorable)",
                      spyValue: spyData?.metrics.omega?.toFixed(2),
                      formula: "Sum(Gains) / Sum(|Losses|)"
                    }}
                 />
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                <section className="glass rounded-3xl p-8">
                  <h3 className="text-xl font-outfit font-bold mb-6 flex items-center justify-between text-white">
                    <span>Drawdown Intensity vs SPY</span>
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">30yr History</span>
                  </h3>
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={inspectionStrategy.curve.dates.map((d, i) => ({
                        date: d,
                        dd: (inspectionStrategy.metrics.drawdowns?.[i] || 0) * 100,
                        spy_dd: (spyData?.metrics.drawdowns?.[i] || 0) * 100
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="date" hide />
                        <YAxis tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} />
                        <RechartsTooltip contentStyle={customTooltipStyle} itemStyle={{ color: '#fff' }} allowEscapeViewBox={{ x: false, y: false }} />
                        <Legend />
                        <Area type="monotone" name="Portfolio DD" dataKey="dd" stroke="#ef4444" fill="rgba(239, 68, 68, 0.15)" strokeWidth={2} />
                        <Area type="monotone" name="SPY DD" dataKey="spy_dd" stroke="#475569" fill="rgba(71, 85, 105, 0.05)" strokeWidth={1} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </section>
                <section className="glass rounded-3xl p-8">
                  <h3 className="text-xl font-outfit font-bold mb-6 text-white">Rolling 1yr Volatility Profile</h3>
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={inspectionStrategy.curve.dates.map((d, i) => ({
                        date: d,
                        vol: inspectionStrategy.metrics.rolling_vol?.[i],
                        spy_vol: spyData?.metrics.rolling_vol?.[i]
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="date" hide />
                        <YAxis tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} />
                        <RechartsTooltip contentStyle={customTooltipStyle} itemStyle={{ color: '#fff' }} allowEscapeViewBox={{ x: false, y: false }} />
                        <Legend />
                        <Line type="monotone" name="Portfolio Vol" dataKey="vol" stroke="#6366f1" dot={false} strokeWidth={2} isAnimationActive={false} />
                        <Line type="monotone" name="SPY Vol" dataKey="spy_vol" stroke="#475569" dot={false} strokeWidth={1} strokeDasharray="5 5" isAnimationActive={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </section>
                <section className="glass rounded-3xl p-8">
                  <h3 className="text-xl font-outfit font-bold mb-6 text-white">Annual Return vs SPY</h3>
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={inspectionStrategy.metrics.yearly_returns.map(yr => ({
                        ...yr,
                        spy_return: spyData?.metrics.yearly_returns.find(s => s.year === yr.year)?.return || 0
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="year" tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} />
                        <YAxis tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} />
                        <RechartsTooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={customTooltipStyle} itemStyle={{ color: '#fff' }} allowEscapeViewBox={{ x: false, y: false }} />
                        <Legend />
                        <Bar dataKey="return" name="Portfolio %">
                          {inspectionStrategy.metrics.yearly_returns.map((entry, index) => (
                            <Cell key={index} fill={entry.return >= 0 ? "rgba(16, 185, 129, 0.8)" : "rgba(239, 68, 68, 0.8)"} />
                          ))}
                        </Bar>
                        <Bar dataKey="spy_return" name="SPY %" fill="rgba(71, 85, 105, 0.3)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>
                <section className="glass rounded-3xl p-8 flex flex-col gap-6">
                  <h3 className="text-xl font-outfit font-bold text-white">Cross-Regime Robustness Audit</h3>
                  <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <AuditCard 
                      title="Resilience Profile (10y Segments)" 
                      audit={inspectionStrategy.resilience} 
                      baselineCagr={inspectionStrategy.metrics.cagr * 100}
                      accentColor="text-accent"
                    />
                    <AuditCard 
                      title="Synthetic Universe Alpha" 
                      audit={inspectionStrategy.synthetic} 
                      baselineCagr={inspectionStrategy.metrics.cagr * 100}
                      accentColor="text-success"
                    />
                  </div>
                  <div className="p-4 rounded-xl bg-accent/10 border border-accent/20 flex gap-3 items-center">
                    <Shield className="text-accent w-5 h-5 shrink-0" />
                    <p className="text-[10px] text-accent font-medium leading-relaxed">Audit run with 50 Monte Carlo iterations across 10-year sliding windows and block-bootstrapped synthetic data series.</p>
                  </div>
                </section>
              </div>
            </motion.div>
          ) : (
            <motion.div key="main" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-10">
              <header className="flex justify-between items-end">
                <div>
                  <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
                    <Globe className="w-4 h-4" />
                    <span>Live Tournament Universe</span>
                  </div>
                  <h2 className="text-4xl font-outfit font-extrabold tracking-tight text-white underline decoration-accent decoration-4 underline-offset-8">Strategy Tournament</h2>
                </div>
                <div className="flex gap-8">
                  <div className="text-right">
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">Global CAGR Lead</p>
                    <p className="text-2xl font-outfit font-bold text-success">{bestCagr ? (bestCagr.metrics.cagr * 100).toFixed(1) : '0.0'}%</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">Tournament Population</p>
                    <p className="text-2xl font-outfit font-bold text-white">{data.length}</p>
                  </div>
                </div>
              </header>
              <section className="glass rounded-[40px] p-10 border-accent/20 shadow-2xl shadow-accent/5">
                <div className="flex justify-between items-center mb-8">
                  <h3 className="text-2xl font-outfit font-bold flex items-center gap-3 text-white"><Activity className="text-accent" /> Cumulative Growth Discovery</h3>
                  <div className="flex bg-white/5 p-1 rounded-xl border border-border">
                    {[{ id: 'log', label: 'Log Scale' }, { id: 'linear', label: 'Linear' }].map(mode => (
                      <button key={mode.id} onClick={() => setScaleMode(mode.id)} className={cn("px-6 py-2 rounded-lg text-xs font-bold transition-all", scaleMode === mode.id ? "bg-accent text-white shadow-lg shadow-accent/20" : "text-slate-500 hover:text-slate-300")}>{mode.label}</button>
                    ))}
                  </div>
                </div>
                <div className="h-[500px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10 }} minTickGap={120} />
                      <YAxis scale={scaleMode === 'log' ? "log" : "auto"} domain={scaleMode === 'log' ? ['auto', 'auto'] : [0, 'auto']} axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10 }} tickFormatter={v => `$${v > 1000 ? (v/1000).toFixed(0) + 'k' : v}`} />
                      <RechartsTooltip contentStyle={customTooltipStyle} itemStyle={{ color: '#fff' }} allowEscapeViewBox={{ x: false, y: false }} />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: '10px', paddingTop: '30px' }} />
                      {selectedNames.map((name, i) => (
                        <Line key={name} type="monotone" dataKey={name} stroke={COLORS[i % COLORS.length]} strokeWidth={name.includes('B&H') ? 1.5 : 3} strokeDasharray={name.includes('B&H') ? "5 5" : ""} dot={false} isAnimationActive={false} />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </section>
              <section className="glass rounded-[40px] overflow-hidden border-white/5">
                <div className="p-10 border-b border-border flex justify-between items-center bg-white/[0.01]">
                  <h3 className="text-2xl font-outfit font-bold text-white">Quantitative Performance Matrix</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left border-collapse">
                    <thead className="bg-white/5 text-[10px] uppercase tracking-widest font-bold text-slate-500">
                      <tr>
                        <th className="px-10 py-6">Comparison</th>
                        <th className="px-6 py-6">Strategy Identity</th>
                        <th className="px-6 py-6">CAGR</th>
                        <th className="px-6 py-6">Sharpe</th>
                        <th className="px-6 py-6">Max DD</th>
                        <th className="px-6 py-6">Leverage Profile</th>
                        <th className="px-6 py-6 text-right pr-10">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.sort((a,b) => b.metrics.cagr - a.metrics.cagr).map((strat, i) => (
                        <tr key={strat.name} className={cn("border-b border-border transition-all hover:bg-white/[0.04] group", selectedNames.includes(strat.name) ? "bg-accent/[0.05]" : "")}>
                          <td className="px-10 py-6">
                            <button onClick={() => toggleStrategy(strat.name)} className={cn("w-6 h-6 rounded-lg border flex items-center justify-center transition-all", selectedNames.includes(strat.name) ? "bg-accent border-accent text-white shadow-lg shadow-accent/20" : "border-slate-700 hover:border-slate-500")}>
                              {selectedNames.includes(strat.name) ? <Check className="w-4 h-4" /> : <Plus className="w-4 h-4 text-slate-600 group-hover:text-slate-400" />}
                            </button>
                          </td>
                          <td className="px-6 py-6 font-semibold text-slate-200">{strat.name}</td>
                          <td className="px-6 py-6 font-outfit font-bold text-success text-lg">{(strat.metrics.cagr * 100).toFixed(2)}%</td>
                          <td className="px-6 py-6 text-slate-400 font-medium">{strat.metrics.sharpe.toFixed(2)}</td>
                          <td className="px-6 py-6 text-danger font-medium">{(strat.metrics.max_dd * 100).toFixed(1)}%</td>
                          <td className="px-6 py-6">
                            <div className="flex h-3 w-32 bg-white/5 rounded-full overflow-hidden p-[1px] border border-white/5">
                              <div style={{ width: `${(strat.metrics.allocation_pct?.['3xSPY'] || 0) * 100}%` }} className="bg-danger h-full" />
                              <div style={{ width: `${(strat.metrics.allocation_pct?.['2xSPY'] || 0) * 100}%` }} className="bg-orange-500 h-full" />
                              <div style={{ width: `${(strat.metrics.allocation_pct?.['SPY'] || 0) * 100}%` }} className="bg-info h-full" />
                              <div style={{ width: `${(strat.metrics.allocation_pct?.['CASH'] || 0) * 100}%` }} className="bg-slate-600 h-full" />
                            </div>
                          </td>
                          <td className="px-6 py-6 text-right pr-10">
                            <button onClick={() => setInspectionStrategy(strat)} className="px-6 py-2 rounded-xl bg-white/5 border border-border text-xs font-bold hover:bg-accent hover:border-accent hover:text-white transition-all shadow-sm">Inspect Audit</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
