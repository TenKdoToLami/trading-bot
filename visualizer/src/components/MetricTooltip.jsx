import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';

export const MetricTooltip = ({ title, explanation, goodRange, spyValue, formula, parentRef, show }) => {
  const [coords, setCoords] = useState({ top: 0, left: 0, flip: false, align: 'center' });
  const tooltipRef = useRef(null);

  useEffect(() => {
    if (show && parentRef.current) {
      const rect = parentRef.current.getBoundingClientRect();
      const tooltipHeight = 240; 
      const tooltipWidth = 288;
      const viewportWidth = window.innerWidth;
      
      let flip = false;
      let top = rect.top + window.scrollY - 8;
      let left = rect.left + rect.width / 2;

      if (rect.top < tooltipHeight + 20) {
        flip = true;
        top = rect.bottom + window.scrollY + 8;
      }

      if (left < tooltipWidth / 2 + 10) {
        left = rect.left;
      } else if (viewportWidth - left < tooltipWidth / 2 + 10) {
        left = rect.right - tooltipWidth;
      } else {
        left = left - tooltipWidth / 2;
      }

      setCoords({ top, left, flip });
    }
  }, [show, parentRef]);

  if (!show) return null;

  return ReactDOM.createPortal(
    <div 
      ref={tooltipRef}
      style={{ 
        position: 'absolute', 
        top: coords.top, 
        left: coords.left, 
        zIndex: 99999,
        pointerEvents: 'none'
      }}
      className="w-72 p-4 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl text-[11px] leading-relaxed space-y-2"
    >
      <p className="font-bold text-accent uppercase tracking-widest border-b border-slate-800 pb-1 mb-1">{title}</p>
      <p className="text-slate-300">{explanation}</p>
      <div className="grid grid-cols-2 gap-2 pt-1">
        <div>
          <p className="text-slate-500 font-bold uppercase text-[9px]">Good Range</p>
          <p className="text-success font-medium">{goodRange}</p>
        </div>
        <div>
          <p className="text-slate-500 font-bold uppercase text-[9px]">SPY (Benchmark)</p>
          <p className="text-info font-medium">{spyValue}</p>
        </div>
      </div>
      <div className="pt-2 border-t border-slate-800">
        <p className="text-slate-500 font-bold uppercase text-[9px]">Formula</p>
        <code className="text-slate-400 font-mono italic">{formula}</code>
      </div>
    </div>,
    document.body
  );
};
