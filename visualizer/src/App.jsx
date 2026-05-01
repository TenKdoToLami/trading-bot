import React, { useState, useEffect, useMemo } from 'react';
import { 
  TrendingUp, Shield, Zap, BarChart3, Activity, Globe, Check, ChevronLeft,
  Plus, Bolt, LineChart as LucideLineChart, Gem, Scale, ExternalLink, Info
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, 
  Legend, AreaChart, Area, BarChart, Bar, Cell, ReferenceArea
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Internal Components
import { RiskGaugeCard } from './components/RiskGaugeCard';
import { AuditCard } from './components/AuditCard';
import { LeverageBar } from './components/LeverageBar';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const MonthlyPerformanceGrid = ({ monthlyReturns }) => {
  if (!monthlyReturns || monthlyReturns.length === 0) return null;

  const years = [...new Set(monthlyReturns.map(m => m.month.split('-')[0]))].sort((a, b) => b - a);
  const months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
  const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  const getReturnColor = (ret) => {
    if (ret > 5) return 'bg-emerald-500/80 text-emerald-50';
    if (ret > 2) return 'bg-emerald-500/40 text-emerald-100';
    if (ret > 0) return 'bg-emerald-500/20 text-emerald-200';
    if (ret < -5) return 'bg-rose-500/80 text-rose-50';
    if (ret < -2) return 'bg-rose-500/40 text-rose-100';
    if (ret < 0) return 'bg-rose-500/20 text-rose-200';
    return 'bg-slate-800 text-slate-500';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-separate border-spacing-1">
        <thead>
          <tr>
            <th className="p-1 text-[10px] text-slate-500 uppercase font-bold text-left">Year</th>
            {monthLabels.map(m => (
              <th key={m} className="p-1 text-[10px] text-slate-500 uppercase font-bold text-center">{m}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {years.map(year => (
            <tr key={year}>
              <td className="p-1 text-xs font-mono font-bold text-slate-300 border-r border-slate-800 pr-2">{year}</td>
              {months.map(month => {
                const data = monthlyReturns.find(m => m.month === `${year}-${month}`);
                const ret = data ? data.return : null;
                return (
                  <td key={month} className={cn("p-2 text-[10px] font-mono font-bold text-center rounded-sm", getReturnColor(ret))}>
                    {ret !== null ? `${ret > 0 ? '+' : ''}${ret.toFixed(1)}%` : '-'}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const COLORS = [
  "#6366f1", "#10b981", "#ef4444", "#3b82f6", "#f59e0b", "#ec4899", "#8b5cf6", "#14b8a6"
];

const REGIME_COLORS = {
  '3x': '#00e676', // Emerald Green
  '2x': '#ffcc00', // Gold/Amber
  '1x': '#3b82f6', // Bright Blue
  'SPY': '#3b82f6',
  'CASH': '#ff4d4d', // Rose Red
  'DEFAULT': '#6366f1'
};

const ArchitectureBanner = ({ version }) => {
  const meta = {
    '9': { name: 'Deep Hysteresis', color: '#8884d8', desc: 'Neural Confidence with Decision Buffering' },
    '7': { name: 'Deep MLP', color: '#82ca9d', desc: 'Multilayer Perceptron Neural Engine' },
    '6': { name: 'Balancer', color: '#ffc658', desc: 'Multi-Brain Portfolio Optimization' },
    '4': { name: 'AI Precision', color: '#ff8042', desc: 'Dual-Brain Conviction Logic (3-State)' },
    '3': { name: 'Precision Binary', color: '#0088fe', desc: 'Dual-Brain Binary Decision Engine' }
  };
  const m = meta[Math.floor(parseFloat(version))?.toString()] || { name: 'Standard Strategy', color: '#ccc', desc: 'Rule-based or Hybrid Logic' };
  return (
    <div style={{ padding: '8px 16px', borderRadius: '8px', borderLeft: `4px solid ${m.color}`, background: 'rgba(255,255,255,0.03)', marginBottom: '20px' }}>
      <div style={{ fontSize: '0.8rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '1px' }}>Architecture: {m.name}</div>
      <div style={{ fontSize: '0.7rem', opacity: 0.4 }}>{m.desc} (v{version})</div>
    </div>
  );
};

const getRegimeColor = (name) => {
  if (!name) return REGIME_COLORS.DEFAULT;
  const upper = name.toUpperCase();
  if (upper.includes('3X')) return REGIME_COLORS['3x'];
  if (upper.includes('2X')) return REGIME_COLORS['2x'];
  if (upper.includes('1X') || upper.includes('NEUTRAL') || upper.includes('SPY')) return REGIME_COLORS['1x'];
  if (upper.includes('CASH') || upper.includes('PANIC')) return REGIME_COLORS.CASH;
  return REGIME_COLORS.DEFAULT;
};

const getInspectionVersion = (strat) => {
  return parseFloat(strat?.parameters?.["Genome Version"] || strat?.parameters?.["version"] || 0);
};

const CustomChartTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const sortedPayload = [...payload].sort((a, b) => b.value - a.value);
    
    // Determine unit based on payload keys
    const isPercentage = payload.some(p => p.name.includes('DD') || p.name.includes('Vol') || p.name.includes('%') || p.name.includes('Growth'));
    const isLeverage = payload.some(p => p.name.includes('Leverage'));
    
    const formatValue = (v) => {
      if (isLeverage) return `${v.toFixed(1)}x`;
      if (isPercentage) return `${v.toFixed(1)}%`;
      if (payload.some(p => p.name.includes('Bullish') || p.name.includes('Panic') || p.name.includes('Neutral'))) {
         return `${(v * 100).toFixed(1)}%`;
      }
      return `${((v - 1) * 100).toLocaleString()}%`; // Growth Curve logic
    };

    return (
      <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-xl p-4 shadow-2xl min-w-[200px]">
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-800 pb-2">{label}</p>
        <div className="space-y-2">
          {sortedPayload.map((entry, index) => (
            <div key={index} className="flex justify-between items-center gap-6">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getRegimeColor(entry.name) }} />
                <span className="text-xs font-semibold text-slate-300">{entry.name}</span>
              </div>
              <span className="text-xs font-mono font-bold" style={{ color: getRegimeColor(entry.name) }}>
                {formatValue(entry.value)}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};
const RegimeDistributionTable = ({ allocation }) => {
  if (!allocation) return null;
  
  const tiers = [
    { key: 'CASH', label: 'Cash (0x)', color: '#ef4444', bg: 'bg-rose-500/20' },
    { key: 'SPY', label: 'Neutral (1x)', color: '#3b82f6', bg: 'bg-blue-500/20' },
    { key: '2xSPY', label: 'Aggressive (2x)', color: '#6366f1', bg: 'bg-indigo-500/20' },
    { key: '3xSPY', label: 'Extreme (3x)', color: '#10b981', bg: 'bg-emerald-500/20' }
  ];

  return (
    <div className="bg-slate-900/40 rounded-3xl p-8 border border-white/5 backdrop-blur-xl">
      <h3 className="text-xl font-outfit font-bold mb-8 flex items-center justify-between text-white">
        <span>Regime Presence Distribution</span>
        <span className="text-[10px] text-accent font-bold uppercase tracking-widest opacity-60">Historical Exposure Analysis</span>
      </h3>
      <div className="space-y-6">
        {tiers.map(tier => {
          const pct = (allocation[tier.key] || 0) * 100;
          return (
            <div key={tier.key} className="space-y-3">
              <div className="flex justify-between items-end">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: tier.color }}></div>
                  <span className="text-sm font-bold text-slate-300 tracking-tight">{tier.label}</span>
                </div>
                <span className="text-lg font-mono font-black text-white">{pct.toFixed(1)}%</span>
              </div>
              <div className="h-2.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
                <div 
                  className={`h-full transition-all duration-1000 ease-out relative`}
                  style={{ width: `${pct}%`, backgroundColor: `${tier.color}4D` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer"></div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-8 pt-8 border-t border-white/5 flex gap-12">
         <div>
            <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Dominant State</div>
            <div className="text-lg font-black text-accent">
              {tiers.reduce((prev, current) => ((allocation[prev.key] || 0) > (allocation[current.key] || 0)) ? prev : current).label.split(' ')[0]}
            </div>
         </div>
         <div>
            <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Tail Risk Zone</div>
            <div className="text-lg font-black text-rose-500">
              {((allocation['CASH'] || 0) * 100).toFixed(1)}%
            </div>
         </div>
      </div>
    </div>
  );
};

const RegimeMatrix = ({ matrix }) => {
  if (!matrix || matrix.length === 0) return null;

  return (
    <section className="glass rounded-3xl p-8 mb-8">
      <h3 className="text-xl font-outfit font-bold mb-6 flex items-center justify-between text-white">
        <span>Volatility Regime Matrix (VIX Buckets)</span>
        <span className="text-[10px] text-accent font-bold uppercase tracking-widest opacity-60">Bucket-Based Allocation</span>
      </h3>
      <div className="grid grid-cols-4 gap-1 bg-white/10 rounded-2xl overflow-hidden border border-white/10 shadow-2xl">
        {/* Header */}
        <div className="p-4 bg-slate-900/80 text-slate-500 text-[10px] font-bold uppercase tracking-widest">Zone</div>
        <div className="p-4 bg-slate-900/80 text-rose-500 text-[10px] font-bold uppercase tracking-widest text-center">Cash (0x)</div>
        <div className="p-4 bg-slate-900/80 text-blue-500 text-[10px] font-bold uppercase tracking-widest text-center">SPY (1x)</div>
        <div className="p-4 bg-slate-900/80 text-emerald-500 text-[10px] font-bold uppercase tracking-widest text-center">3x SPY (Bull)</div>

        {/* Rows */}
        {matrix.map((row, idx) => (
          <React.Fragment key={idx}>
            <div className="p-5 bg-white/5 text-white text-sm font-bold border-t border-white/5">{row.label}</div>
            <div 
              className="p-5 flex items-center justify-center text-lg font-black border-t border-white/5 transition-all hover:brightness-125"
              style={{ backgroundColor: `rgba(239, 68, 68, ${row.cash * 0.4 + 0.05})`, color: row.cash > 0.5 ? '#fff' : '#ef4444' }}
            >
              {Math.round(row.cash * 100)}%
            </div>
            <div 
              className="p-5 flex items-center justify-center text-lg font-black border-t border-white/5 transition-all hover:brightness-125"
              style={{ backgroundColor: `rgba(59, 130, 246, ${row.spy * 0.4 + 0.05})`, color: row.spy > 0.5 ? '#fff' : '#3b82f6' }}
            >
              {Math.round(row.spy * 100)}%
            </div>
            <div 
              className="p-5 flex items-center justify-center text-lg font-black border-t border-white/5 transition-all hover:brightness-125"
              style={{ backgroundColor: `rgba(16, 185, 129, ${row.triple * 0.4 + 0.05})`, color: row.triple > 0.5 ? '#fff' : '#10b981' }}
            >
              {Math.round(row.triple * 100)}%
            </div>
          </React.Fragment>
        ))}
      </div>
      <div className="mt-6 flex items-center gap-3 p-4 bg-white/5 rounded-xl border border-white/5">
        <Info className="w-4 h-4 text-accent" />
        <p className="text-[11px] text-slate-400 font-medium leading-relaxed italic">
          This matrix represents the fixed allocation rules of the V1/V2 series. The strategy automatically pivots between these rows based on real-time VIX volatility readings, overlaid with a primary trend filter.
        </p>
      </div>
    </section>
  );
};

const IndicatorSensitivityTable = ({ indicators }) => {
  if (!indicators || indicators.length === 0) return null;

  // Sort by priority (max of bull or panic)
  const sorted = [...indicators].sort((a, b) => {
    const maxA = a.priority || 0;
    const maxB = b.priority || 0;
    return maxB - maxA;
  });

  const maxWeight = Math.max(...sorted.map(i => i.priority), 0.001);

  return (
    <div className="space-y-4">
      {sorted.map((ind, idx) => {
        const isDual = ind.panic_priority !== undefined;
        const pct = (ind.priority / maxWeight) * 100;
        
        return (
          <div key={idx} className="group flex items-center gap-6">
            {/* Label & Meta */}
            <div className="w-48 shrink-0">
              <div className="flex flex-col">
                <span className="text-xs font-black text-white group-hover:text-accent transition-colors truncate">
                  {ind.name}
                </span>
                <span className="text-[9px] text-slate-500 font-bold uppercase tracking-tighter">
                  {isDual ? "Multi-Brain Driver" : "Neural Vector"}
                </span>
              </div>
            </div>

            {/* Bar Track */}
            <div className="flex-1 h-3 bg-white/5 rounded-full overflow-hidden border border-white/5 relative group-hover:border-white/10 transition-all">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 1, delay: idx * 0.05, ease: "circOut" }}
                className={cn(
                  "h-full relative",
                  isDual ? "bg-gradient-to-r from-amber-500/40 to-amber-500" : "bg-gradient-to-r from-accent/40 to-accent"
                )}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
              </motion.div>
            </div>

            {/* Value */}
            <div className="w-16 text-right">
              <span className="text-[10px] font-mono font-black text-slate-400 group-hover:text-white transition-colors">
                {ind.priority.toFixed(3)}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

const NeuralDecisionMatrix = ({ strategy }) => {
  const trace = strategy.telemetry?.signal_trace;
  if (!trace) return null;

  const rows = [
    { label: 'Panic State', brain: 'Panic Brain', key: 'p', color: 'text-rose-500', bg: 'bg-rose-500/10', target: 'CASH (0x)' },
    { label: 'Extreme Bull', brain: 'Bull Brain', key: 'b', color: 'text-emerald-500', bg: 'bg-emerald-500/10', target: '3x SPY' },
    { label: 'Aggressive', brain: '2x Brain', key: 's2', color: 'text-blue-500', bg: 'bg-blue-500/10', target: '2x SPY' },
    { label: 'Neutral', brain: '1x Brain', key: 's1', color: 'text-slate-400', bg: 'bg-slate-400/10', target: '1x SPY' }
  ].filter(r => trace[0][`${r.key}_score`] !== undefined);

  return (
    <section className="glass rounded-3xl p-8 mb-8">
      <h3 className="text-xl font-outfit font-bold mb-6 flex items-center justify-between text-white">
        <span>Neural Decision Matrix</span>
        <span className="text-[10px] text-accent font-bold uppercase tracking-widest opacity-60">Rules of Engagement</span>
      </h3>
      <div className="overflow-hidden rounded-2xl border border-white/5 bg-slate-900/40">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-white/5">
              <th className="p-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Logic Tier</th>
              <th className="p-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest text-center">Trigger Condition</th>
              <th className="p-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest text-center">Brain Sensitivity</th>
              <th className="p-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest text-right">Target Regime</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rows.map((row, idx) => {
              const thresh = trace[0][`${row.key}_thresh`] || 0;
              return (
                <tr key={idx} className="hover:bg-white/5 transition-colors group">
                  <td className="p-4">
                    <div className="flex flex-col">
                      <span className={`text-sm font-black ${row.color}`}>{row.label}</span>
                      <span className="text-[10px] text-slate-500 font-bold uppercase">{row.brain}</span>
                    </div>
                  </td>
                  <td className="p-4 text-center">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                      <span className="text-[10px] font-bold text-slate-400">Score &gt;</span>
                      <span className="text-xs font-mono font-bold text-white">{thresh.toFixed(2)}</span>
                    </div>
                  </td>
                  <td className="p-4 text-center">
                    <div className="w-24 h-1.5 bg-white/5 rounded-full mx-auto overflow-hidden">
                      <div 
                        className={`h-full ${row.color.replace('text-', 'bg-')} opacity-60 transition-all duration-1000`} 
                        style={{ width: `${Math.min(100, (1/thresh) * 50)}%` }}
                      ></div>
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <span className="text-xs font-black text-white bg-white/5 px-3 py-1.5 rounded-lg border border-white/10 group-hover:border-accent/40 transition-all">
                      {row.target}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
};

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
        const defaultSelected = json.filter(s => s.name.includes('[BASE]')).map(s => s.name);
        setSelectedNames(defaultSelected.length ? defaultSelected : json.slice(0, 3).map(s => s.name));
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load data:", err);
        fetch('/data.json')
          .then(res => res.json())
          .then(json => {
            setData(json);
            const defaultSelected = json.filter(s => s.name.includes('[BASE]')).map(s => s.name);
            setSelectedNames(defaultSelected.length ? defaultSelected : json.slice(0, 3).map(s => s.name));
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
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getRegimeColor(strat.name) }} />
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

              <ArchitectureBanner version={getInspectionVersion(inspectionStrategy)} />

              {/* Version-Specific Conviction Fight (V3/V4) */}
              {getInspectionVersion(inspectionStrategy) >= 3 && getInspectionVersion(inspectionStrategy) < 5 && inspectionStrategy.telemetry?.monthly_avg && (
                <div className="card mb-6 bg-slate-900/50 border-accent/20">
                  <div className="flex items-center justify-between p-4 border-b border-white/5">
                    <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400"> Conviction Fight: Panic vs Bull</h3>
                  </div>
                  <div className="p-6 grid grid-cols-2 gap-8">
                    <div className="space-y-2">
                       <div className="flex justify-between text-[10px] font-bold text-slate-500 uppercase">
                          <span>Panic Brain Conviction</span>
                          <span className="text-red-400">{(Object.values(inspectionStrategy.telemetry.monthly_avg).slice(-1)[0]?.conf_cash * 100).toFixed(1)}%</span>
                       </div>
                       <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                          <div className="h-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)] transition-all duration-1000" style={{ width: `${(Object.values(inspectionStrategy.telemetry.monthly_avg).slice(-1)[0]?.conf_cash * 100)}%` }}></div>
                       </div>
                    </div>
                    <div className="space-y-2">
                       <div className="flex justify-between text-[10px] font-bold text-slate-500 uppercase">
                          <span>Bull Brain Conviction</span>
                          <span className="text-emerald-400">{(Object.values(inspectionStrategy.telemetry.monthly_avg).slice(-1)[0]?.conf_3x * 100).toFixed(1)}%</span>
                       </div>
                       <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] transition-all duration-1000" style={{ width: `${(Object.values(inspectionStrategy.telemetry.monthly_avg).slice(-1)[0]?.conf_3x * 100)}%` }}></div>
                       </div>
                    </div>
                  </div>
                </div>
              )}

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

              <div className="flex flex-col gap-8">
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
                        <defs>
                          <linearGradient id="ddGradient" x1="0" y1="0" x2="1" y2="0">
                            {inspectionStrategy.curve.dates.map((_, i, arr) => {
                              const dd = (inspectionStrategy.metrics.drawdowns?.[i] || 0);
                              const spy_dd = (spyData?.metrics.drawdowns?.[i] || 0);
                              const color = dd >= spy_dd ? "#10b981" : "#ef4444"; // Green if better (less negative), Red if worse
                              return <stop key={i} offset={`${(i / arr.length) * 100}%`} stopColor={color} />;
                            })}
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="date" hide />
                        <YAxis tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} />
                        <RechartsTooltip content={<CustomChartTooltip />} allowEscapeViewBox={{ x: false, y: false }} />
                        <Legend />
                        <Area type="monotone" name="Portfolio DD" dataKey="dd" stroke="url(#ddGradient)" fill="rgba(255, 255, 255, 0.05)" strokeWidth={2} />
                        <Area type="monotone" name="SPY DD" dataKey="spy_dd" stroke="#475569" fill="rgba(71, 85, 105, 0.02)" strokeWidth={1} />
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
                        <RechartsTooltip content={<CustomChartTooltip />} allowEscapeViewBox={{ x: false, y: false }} />
                        <Legend />
                        <Line type="monotone" name="Portfolio Vol" dataKey="vol" stroke={getRegimeColor(inspectionStrategy.name)} dot={false} strokeWidth={2} isAnimationActive={false} />
                        <Line type="monotone" name="SPY Vol" dataKey="spy_vol" stroke={REGIME_COLORS.SPY} dot={false} strokeWidth={1} strokeDasharray="5 5" isAnimationActive={false} />
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
                          {inspectionStrategy.metrics.yearly_returns.map((entry, index) => {
                            const spyReturn = spyData?.metrics.yearly_returns.find(s => s.year === entry.year)?.return || 0;
                            const isBeatingSpy = entry.return > spyReturn;
                            return (
                              <Cell 
                                key={index} 
                                fill={isBeatingSpy ? "rgba(16, 185, 129, 0.8)" : "rgba(239, 68, 68, 0.8)"} 
                              />
                            );
                          })}
                        </Bar>
                        <Bar dataKey="spy_return" name="SPY %" fill={`${REGIME_COLORS.SPY}4D`} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>

                <section className="glass rounded-3xl p-8">
                  <h3 className="text-xl font-outfit font-bold mb-6 flex items-center justify-between text-white">
                    <span>Regime-Aware Log Performance</span>
                    <div className="flex gap-4 text-[8px] font-bold uppercase tracking-widest opacity-60">
                      <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-danger/20 border border-danger/40"/> 3x</span>
                      <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-success/20 border border-success/40"/> 2x</span>
                      <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-info/20 border border-info/40"/> 1x</span>
                      <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-slate-800/20 border border-slate-700/40"/> CASH</span>
                    </div>
                  </h3>
                  <div className="h-96">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={inspectionStrategy.curve.dates.map((d, i) => ({
                        date: d,
                        equity: inspectionStrategy.curve.equities[i],
                        spy_equity: spyData?.curve.equities[i]
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="date" hide />
                        <YAxis scale="log" domain={['auto', 'auto']} tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={v => `${((v - 1) * 100).toLocaleString()}%`} />
                        <RechartsTooltip content={<CustomChartTooltip />} allowEscapeViewBox={{ x: false, y: false }} />
                        
                        {/* Regime Highlights */}
                        {(() => {
                          const dates = inspectionStrategy.curve.dates;
                          const regimes = inspectionStrategy.history?.regime;
                          if (!dates || !regimes) return null;
                          const spans = [];
                          let currentStart = dates[0];
                          let currentRegime = regimes[0];
                          for (let i = 1; i < dates.length; i++) {
                            if (regimes[i] !== currentRegime) {
                              spans.push({ x1: currentStart, x2: dates[i], regime: currentRegime });
                              currentStart = dates[i];
                              currentRegime = regimes[i];
                            }
                          }
                          spans.push({ x1: currentStart, x2: dates[dates.length - 1], regime: currentRegime });
                          
                          const colors = {
                            '3xSPY': 'rgba(239, 68, 68, 0.35)',
                            '2xSPY': 'rgba(16, 185, 129, 0.35)',
                            'SPY': 'rgba(59, 130, 246, 0.35)',
                            'CASH': 'rgba(71, 85, 105, 0.45)'
                          };
                          
                          return spans.map((s, idx) => (
                            <ReferenceArea key={idx} x1={s.x1} x2={s.x2} fill={colors[s.regime] || 'transparent'} stroke="none" />
                          ));
                        })()}
                        
                        <Area type="monotone" name="Portfolio (Log)" dataKey="equity" stroke={getRegimeColor(inspectionStrategy.name)} fill={`${getRegimeColor(inspectionStrategy.name)}1A`} strokeWidth={3} />
                        <Area type="monotone" name="SPY (Log)" dataKey="spy_equity" stroke="#475569" fill="transparent" strokeWidth={1} strokeDasharray="5 5" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </section>

                <section className="glass rounded-3xl p-8">
                  <h3 className="text-xl font-outfit font-bold mb-6 flex items-center justify-between text-white">
                    <span>Leverage Development History</span>
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Dynamic Exposure Audit</span>
                  </h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={inspectionStrategy.curve.dates.map((d, i) => ({
                        date: d,
                        leverage: inspectionStrategy.history?.leverage[i] || 0
                      }))}>
                        <defs>
                          <linearGradient id="levGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="date" hide />
                        <YAxis domain={[0, 3.5]} tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={v => `${v.toFixed(1)}x`} />
                        <RechartsTooltip content={<CustomChartTooltip />} allowEscapeViewBox={{ x: false, y: false }} />
                        <Area type="stepAfter" name="Leverage" dataKey="leverage" stroke="#6366f1" fill="url(#levGradient)" strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </section>

                <section className="glass rounded-3xl p-8 mb-8">
                  <h3 className="text-xl font-outfit font-bold mb-6 flex items-center justify-between text-white">
                    <span>Decision Engine Anatomy</span>
                    <span className="text-[10px] text-accent font-bold uppercase tracking-widest opacity-60">Logic & Feature DNA</span>
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                    <div className="p-6 bg-white/5 rounded-2xl border border-white/10 group hover:border-accent/40 transition-all">
                      <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-2">Lock Days</div>
                      <div className="text-2xl font-mono font-black text-white group-hover:text-accent transition-colors">
                        {(inspectionStrategy.genome?.lock_days || 0).toFixed(1)}
                      </div>
                    </div>
                    <div className="p-6 bg-white/5 rounded-2xl border border-white/10 group hover:border-accent/40 transition-all">
                      <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-2">Genome Version</div>
                      <div className="text-2xl font-mono font-black text-white group-hover:text-accent transition-colors">
                        {inspectionStrategy.genome?.version || "1.0"}
                      </div>
                    </div>
                  </div>

                  {/* Regime Presence Table */}
                  <RegimeDistributionTable allocation={inspectionStrategy.metrics?.allocation_pct} />

                  <div className="mt-8">
                    <h4 className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">Neural Score Logic (Indicator Weights)</h4>
                    <IndicatorSensitivityTable indicators={inspectionStrategy.indicators} />
                  </div>
                </section>

                {/* Only show Regime Mix for strategies without high-fidelity signal traces */}
                {inspectionStrategy.telemetry && inspectionStrategy.telemetry.monthly_avg && !inspectionStrategy.telemetry.signal_trace && (
                  <section className="glass rounded-3xl p-8">
                    <h3 className="text-xl font-outfit font-bold mb-6 flex items-center justify-between text-white">
                      <span>Neural Regime Mix (Monthly Aggregated)</span>
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Smoothed Decision Environment</span>
                    </h3>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart 
                          data={
                            Array.isArray(inspectionStrategy.telemetry.monthly_avg) 
                              ? inspectionStrategy.telemetry.monthly_avg 
                              : Object.entries(inspectionStrategy.telemetry.monthly_avg).map(([month, val]) => ({ month, ...val }))
                          }
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                          <XAxis dataKey="month" hide />
                          <YAxis 
                            tick={{ fill: '#64748b', fontSize: 10 }} 
                            domain={[0, 1]} 
                            tickFormatter={v => `${(v * 100).toFixed(0)}%`} 
                          />
                          <RechartsTooltip content={<CustomChartTooltip />} />
                          <Bar dataKey="conf_3x" name="Bullish 3x" stackId="1" fill={REGIME_COLORS['3x']} fillOpacity={0.8} />
                          <Bar dataKey="conf_2x" name="Aggressive 2x" stackId="1" fill={REGIME_COLORS['2x']} fillOpacity={0.8} />
                          <Bar dataKey="conf_1x" name="Neutral 1x" stackId="1" fill={REGIME_COLORS['1x']} fillOpacity={0.8} />
                          <Bar dataKey="conf_cash" name="Panic/Cash" stackId="1" fill={REGIME_COLORS['CASH']} fillOpacity={0.8} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </section>
                )}

                {/* Volatility Regime Matrix (V1/V2 Legacy) */}
                {inspectionStrategy.telemetry?.regime_matrix && (
                  <RegimeMatrix matrix={inspectionStrategy.telemetry.regime_matrix} />
                )}

                {/* Neural Decision Matrix */}
                {inspectionStrategy.telemetry?.signal_trace && (
                  <NeuralDecisionMatrix strategy={inspectionStrategy} />
                )}

                <section className="glass rounded-3xl p-8">
                  <h3 className="text-xl font-outfit font-bold mb-6 flex items-center justify-between text-white">
                    <span>Monthly Returns Matrix</span>
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Institutional Alpha Audit</span>
                  </h3>
                  <MonthlyPerformanceGrid monthlyReturns={inspectionStrategy.metrics.monthly_returns} />
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
                      <YAxis scale={scaleMode === 'log' ? "log" : "auto"} domain={scaleMode === 'log' ? ['auto', 'auto'] : [1, 'auto']} axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10 }} tickFormatter={v => `${((v-1)*100).toFixed(0)}%`} />
                      <RechartsTooltip content={<CustomChartTooltip />} allowEscapeViewBox={{ x: false, y: false }} />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: '10px', paddingTop: '30px' }} />
                      {selectedNames.map((name, i) => (
                        <Line key={name} type="monotone" dataKey={name} stroke={getRegimeColor(name)} strokeWidth={name.includes('B&H') ? 1.5 : 3} strokeDasharray={name.includes('B&H') ? "5 5" : ""} dot={false} isAnimationActive={false} />
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
                        <th className="px-10 py-6">Strategy Identity</th>
                        <th className="px-6 py-6 text-center">CAGR</th>
                        <th className="px-6 py-6 text-center">Sharpe</th>
                        <th className="px-6 py-6 text-center">Calmar</th>
                        <th className="px-6 py-6 text-center">Volat.</th>
                        <th className="px-6 py-6 text-center">Max DD</th>
                        <th className="px-6 py-6 text-center">Pivots/Yr</th>
                        <th className="px-6 py-6">
                          <div className="flex flex-col gap-1">
                            <span>Leverage Profile</span>
                            <div className="flex gap-2 text-[8px] font-bold uppercase tracking-tighter opacity-70">
                              <span className="flex items-center gap-0.5"><div className="w-1.5 h-1.5 rounded-full bg-danger"/> 3x</span>
                              <span className="flex items-center gap-0.5"><div className="w-1.5 h-1.5 rounded-full bg-success"/> 2x</span>
                              <span className="flex items-center gap-0.5"><div className="w-1.5 h-1.5 rounded-full bg-info"/> 1x</span>
                              <span className="flex items-center gap-0.5"><div className="w-1.5 h-1.5 rounded-full bg-slate-600"/> CASH</span>
                            </div>
                          </div>
                        </th>
                        <th className="px-6 py-6 text-right pr-10">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.sort((a,b) => b.metrics.cagr - a.metrics.cagr).map((strat, i) => (
                        <tr key={strat.name} className={cn("border-b border-border transition-all hover:bg-white/[0.04] group", selectedNames.includes(strat.name) ? "bg-accent/[0.05]" : "")}>
                          <td className="px-10 py-6 font-semibold text-slate-200">{strat.name}</td>
                          <td className="px-6 py-6 font-outfit font-bold text-success text-lg text-center">{(strat.metrics.cagr * 100).toFixed(1)}%</td>
                          <td className="px-6 py-6 text-slate-400 font-medium text-center">{strat.metrics.sharpe.toFixed(2)}</td>
                          <td className="px-6 py-6 text-accent font-medium text-center">{strat.metrics.calmar?.toFixed(2) || 'N/A'}</td>
                          <td className="px-6 py-6 text-slate-500 font-medium text-center">{(strat.metrics.volatility * 100).toFixed(1)}%</td>
                          <td className="px-6 py-6 text-danger font-medium text-center">{(strat.metrics.max_dd * 100).toFixed(1)}%</td>
                          <td className="px-6 py-6 text-slate-500 font-medium text-center">{strat.metrics.trades_per_year?.toFixed(1)}</td>
                          <td className="px-6 py-6">
                            <LeverageBar allocation={strat.metrics.allocation_pct} />
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
