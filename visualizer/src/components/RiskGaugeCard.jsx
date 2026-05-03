import React, { useState, useRef } from 'react';
import { Info } from 'lucide-react';
import { MetricTooltip } from './MetricTooltip';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export const RiskGaugeCard = ({ title, value, compareValue, compareLabel, subValue, icon: Icon, colorClass, compareColorClass, progress, trackClass, tooltipProps }) => {
  const cardRef = useRef(null);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div 
      ref={cardRef} 
      className="bg-card border border-border rounded-2xl p-4 flex flex-col gap-2 glass min-w-[160px] flex-1 relative group transition-all hover:bg-white/[0.02]"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex justify-between items-center text-slate-500">
        <div className="flex items-center gap-1.5">
          {Icon && <Icon className="w-3.5 h-3.5" />}
          <span className="text-[10px] font-bold uppercase tracking-widest">{title}</span>
        </div>
        <div className="relative">
          <Info className="w-3 h-3 cursor-help opacity-30 group-hover:opacity-100 transition-opacity" />
        </div>
      </div>
      <div className="flex items-end gap-3">
        <div className={cn("text-2xl font-outfit font-bold", colorClass || "text-slate-200")}>
          {value}
        </div>
        {compareValue !== undefined && (
          <div className="flex flex-col pb-0.5">
             <div className="text-[8px] font-bold uppercase tracking-widest text-slate-500 mb-[1px]">{compareLabel || 'VS COMPARE'}</div>
             <div className={cn("text-lg font-outfit font-bold", compareColorClass || "text-slate-400")}>
               {compareValue}
             </div>
          </div>
        )}
      </div>
      {progress !== undefined && (
        <div className="mt-1">
          <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden relative border border-white/5">
            <div className={cn("h-full absolute left-0 top-0 rounded-full", trackClass || "bg-accent")} style={{ width: `${Math.min(100, Math.max(0, progress))}%` }} />
          </div>
        </div>
      )}
      {subValue && <div className="text-[10px] text-slate-500 font-medium truncate">{subValue}</div>}
      
      {tooltipProps && (
        <MetricTooltip 
          {...tooltipProps} 
          title={title} 
          parentRef={cardRef} 
          show={isHovered} 
        />
      )}
    </div>
  );
};
