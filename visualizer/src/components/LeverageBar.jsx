import React, { useState, useRef } from 'react';
import { SimpleTooltip } from './SimpleTooltip';

export const LeverageBar = ({ allocation }) => {
  const [show, setShow] = useState(false);
  const barRef = useRef(null);

  if (!allocation) return null;

  const tooltipContent = (
    <>
      <div className="flex justify-between gap-4">
        <span className="text-danger font-bold">3x SPY:</span>
        <span className="text-white font-mono">{(allocation['3xSPY'] * 100 || 0).toFixed(1)}%</span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-success font-bold">2x SPY:</span>
        <span className="text-white font-mono">{(allocation['2xSPY'] * 100 || 0).toFixed(1)}%</span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-info font-bold">1x SPY:</span>
        <span className="text-white font-mono">{(allocation['SPY'] * 100 || 0).toFixed(1)}%</span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-slate-500 font-bold">CASH:</span>
        <span className="text-white font-mono">{(allocation['CASH'] * 100 || 0).toFixed(1)}%</span>
      </div>
    </>
  );

  return (
    <div 
      ref={barRef}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
      className="flex h-3 w-32 bg-white/5 rounded-full overflow-hidden p-[1px] border border-white/5 cursor-help relative"
    >
      <div style={{ width: `${(allocation['3xSPY'] || 0) * 100}%` }} className="bg-danger h-full" />
      <div style={{ width: `${(allocation['2xSPY'] || 0) * 100}%` }} className="bg-success h-full" />
      <div style={{ width: `${(allocation['SPY'] || 0) * 100}%` }} className="bg-info h-full" />
      <div style={{ width: `${(allocation['CASH'] || 0) * 100}%` }} className="bg-slate-600 h-full" />
      
      <SimpleTooltip 
        show={show} 
        parentRef={barRef} 
        content={tooltipContent} 
      />
    </div>
  );
};
