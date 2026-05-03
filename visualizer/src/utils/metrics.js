/**
 * Mathematical utilities to recalculate core metrics in the browser dynamically.
 * These mirror the Python empyrical calculations for sliced timeframes.
 */

export const calculateMultiplier = (equities) => {
  if (!equities || equities.length < 2) return 0;
  const start = equities[0];
  const end = equities[equities.length - 1];
  if (start <= 0) return 0;
  return end / start;
};

export const calculateCAGR = (equities, dates) => {
  if (!equities || equities.length < 2 || !dates || dates.length < 2) return 0;
  const multiplier = calculateMultiplier(equities);
  
  const startD = new Date(dates[0]).getTime();
  const endD = new Date(dates[dates.length - 1]).getTime();
  const years = (endD - startD) / (1000 * 60 * 60 * 24 * 365.25);
  
  if (years <= 0) return 0;
  return Math.pow(multiplier, 1 / years) - 1;
};

export const calculateMaxDrawdown = (equities) => {
  if (!equities || equities.length === 0) return 0;
  let maxEquity = equities[0];
  let maxDd = 0;

  for (let i = 0; i < equities.length; i++) {
    const equity = equities[i];
    if (equity > maxEquity) {
      maxEquity = equity;
    }
    const dd = (equity - maxEquity) / maxEquity;
    if (dd < maxDd) {
      maxDd = dd;
    }
  }
  return maxDd;
};

export const calculateDailyReturns = (equities) => {
  const returns = [];
  for (let i = 1; i < equities.length; i++) {
    returns.push((equities[i] - equities[i - 1]) / equities[i - 1]);
  }
  return returns;
};

export const calculateVolatility = (equities, dates) => {
  const returns = calculateDailyReturns(equities);
  if (returns.length < 2 || !dates || dates.length < 2) return 0;
  
  const startD = new Date(dates[0]).getTime();
  const endD = new Date(dates[dates.length - 1]).getTime();
  const years = (endD - startD) / (1000 * 60 * 60 * 24 * 365.25);
  const frequency = equities.length / (years || 1);
  
  const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
  const variance = returns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (returns.length - 1);
  const dailyVol = Math.sqrt(variance);
  
  return dailyVol * Math.sqrt(frequency); // Annualized
};

export const calculateSharpe = (equities, dates, riskFreeRate = 0.0) => {
  const returns = calculateDailyReturns(equities);
  if (returns.length < 2 || !dates || dates.length < 2) return 0;

  const startD = new Date(dates[0]).getTime();
  const endD = new Date(dates[dates.length - 1]).getTime();
  const years = (endD - startD) / (1000 * 60 * 60 * 24 * 365.25);
  const frequency = equities.length / (years || 1);

  const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
  const variance = returns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (returns.length - 1);
  const stdDev = Math.sqrt(variance);

  if (stdDev === 0) return 0;

  const annualizedMean = mean * frequency;
  const annualizedStdDev = stdDev * Math.sqrt(frequency);

  return (annualizedMean - riskFreeRate) / annualizedStdDev;
};

export const calculateCalmar = (equities, dates) => {
  const cagr = calculateCAGR(equities, dates);
  const maxDd = Math.abs(calculateMaxDrawdown(equities));
  if (maxDd === 0) return cagr > 0 ? 999 : 0;
  return cagr / maxDd;
};

export const calculateDrawdownCurve = (equities) => {
  if (!equities || equities.length === 0) return [];
  let maxEq = equities[0];
  const drawdowns = new Array(equities.length);
  
  for (let i = 0; i < equities.length; i++) {
    const eq = equities[i];
    if (eq > maxEq) maxEq = eq;
    drawdowns[i] = (eq - maxEq) / maxEq;
  }
  return drawdowns;
};

export const calculateMonthlyReturns = (dates, equities) => {
  if (!dates || !equities || dates.length !== equities.length) return [];
  
  const monthlyMap = new Map();
  let currentMonth = null;
  let startEq = null;
  
  for (let i = 0; i < dates.length; i++) {
    const dateStr = dates[i];
    const monthStr = dateStr.substring(0, 7); // YYYY-MM
    
    if (monthStr !== currentMonth) {
      currentMonth = monthStr;
      startEq = equities[i];
    }
    
    const endEq = equities[i];
    const ret = ((endEq - startEq) / startEq) * 100; // in percentage
    monthlyMap.set(monthStr, ret);
  }
  
  return Array.from(monthlyMap.entries()).map(([month, ret]) => ({
    month,
    return: ret
  }));
};

export const calculateYearlyReturns = (dates, equities) => {
  if (!dates || !equities || dates.length !== equities.length) return [];
  
  const yearlyMap = new Map();
  let currentYear = null;
  let startEq = null;
  
  for (let i = 0; i < dates.length; i++) {
    const dateStr = dates[i];
    const yearStr = dateStr.substring(0, 4); // YYYY
    
    if (yearStr !== currentYear) {
      currentYear = yearStr;
      startEq = equities[i];
    }
    
    const endEq = equities[i];
    const ret = ((endEq - startEq) / startEq) * 100; // in percentage
    yearlyMap.set(yearStr, ret);
  }
  
  return Array.from(yearlyMap.entries()).map(([year, ret]) => ({
    year: parseInt(year, 10),
    return: ret
  }));
};

/**
 * Returns a new metrics object by calculating core metrics from an equity slice.
 */
export const calculateCoreMetrics = (equities, dates) => {
  return {
    multiplier: calculateMultiplier(equities),
    cagr: calculateCAGR(equities, dates),
    max_dd: calculateMaxDrawdown(equities),
    volatility: calculateVolatility(equities, dates),
    sharpe: calculateSharpe(equities, dates),
    calmar: calculateCalmar(equities, dates),
    drawdowns: calculateDrawdownCurve(equities),
    yearly_returns: calculateYearlyReturns(dates, equities),
    monthly_returns: calculateMonthlyReturns(dates, equities),
    // Nullify advanced metrics that we aren't calculating
    alpha: null,
    beta: null,
    sortino: null,
    omega: null,
    treynor: null,
    information_ratio: null,
    expectancy: null, 
    avg_leverage: null, 
    trades_per_year: null
  };
};
