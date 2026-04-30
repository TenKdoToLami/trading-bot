import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';

export const SimpleTooltip = ({ content, parentRef, show }) => {
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  
  useEffect(() => {
    if (show && parentRef.current) {
      const rect = parentRef.current.getBoundingClientRect();
      setCoords({
        top: rect.top + window.scrollY - 10,
        left: rect.left + rect.width / 2
      });
    }
  }, [show, parentRef]);

  if (!show) return null;

  return ReactDOM.createPortal(
    <div 
      style={{ 
        position: 'absolute', 
        top: coords.top, 
        left: coords.left, 
        transform: 'translate(-50%, -100%)',
        zIndex: 99999,
        pointerEvents: 'none'
      }}
      className="bg-slate-900 border border-slate-700 rounded-lg shadow-2xl p-3 text-[10px] min-w-[140px] whitespace-pre-line leading-relaxed"
    >
      <p className="font-bold text-accent uppercase tracking-widest border-b border-slate-800 pb-1 mb-2">Leverage Profile</p>
      <div className="text-slate-300 space-y-1">
        {content}
      </div>
      {/* Arrow */}
      <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-slate-900" />
    </div>,
    document.body
  );
};
