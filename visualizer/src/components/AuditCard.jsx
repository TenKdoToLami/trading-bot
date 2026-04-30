import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export const AuditCard = ({ title, audit, baselineCagr, accentColor }) => {
  if (!audit) return (
    <div className="p-6 rounded-2xl bg-white/5 border border-border flex flex-col justify-center items-center h-full min-h-[200px] border-dashed">
      <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">Audit Pending</p>
    </div>
  );

  const stability = (audit.avg_cagr / baselineCagr) * 100;

  return (
    <div className="p-6 rounded-2xl bg-white/5 border border-border flex flex-col gap-4">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">{title}</p>
          <h4 className="text-2xl font-bold font-outfit text-white">{audit.avg_cagr.toFixed(1)}% <span className="text-xs text-slate-500 font-normal">avg cagr</span></h4>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Stability</p>
          <p className={cn("text-sm font-bold", accentColor)}>{stability.toFixed(0)}%</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <div className="flex justify-between text-[10px] border-b border-white/5 pb-1">
             <span className="text-slate-500">Median CAGR</span>
             <span className="text-slate-300 font-bold">{audit.med_cagr.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between text-[10px] border-b border-white/5 pb-1">
             <span className="text-slate-500">Max DD (Avg)</span>
             <span className="text-danger font-bold">{audit.avg_dd.toFixed(1)}%</span>
          </div>
        </div>
        <div className="space-y-1">
          <div className="flex justify-between text-[10px] border-b border-white/5 pb-1">
             <span className="text-slate-500">Sharpe (Avg)</span>
             <span className="text-accent font-bold">{audit.avg_sharpe.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-[10px] border-b border-white/5 pb-1">
             <span className="text-slate-500">Volat. (Avg)</span>
             <span className="text-info font-bold">{audit.avg_volatility?.toFixed(1)}%</span>
          </div>
        </div>
      </div>

      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden mt-2">
         <div className={cn("h-full", accentColor.replace('text-', 'bg-'))} style={{ width: `${Math.min(100, stability)}%` }} />
      </div>
    </div>
  );
};
