// frontend/src/lib/mockData.ts
import type { Candle, Stock, StockDetail, CandlePattern, MultiframeSignal, OrderBookEntry, PortfolioMetrics, Holding } from '@/types'

export const MOCK_STOCKS: Stock[] = [
  { code: '005930', name: '삼성전자', price: 73400, change_pct: 1.2 },
  { code: '000660', name: 'SK하이닉스', price: 185000, change_pct: -0.5 },
  { code: '035420', name: 'NAVER', price: 210000, change_pct: 0.8 },
  { code: '035720', name: '카카오', price: 42100, change_pct: -1.3 },
  { code: '051910', name: 'LG화학', price: 320000, change_pct: 2.1 },
]

export const MOCK_WATCHLIST = ['005930', '000660', '035420']

function generateCandles(basePrice: number, count: number): Candle[] {
  const candles: Candle[] = []
  let price = basePrice
  const start = new Date('2026-01-02')

  for (let i = 0; i < count; i++) {
    const date = new Date(start)
    date.setDate(start.getDate() + i)
    if (date.getDay() === 0 || date.getDay() === 6) continue

    const change = (Math.random() - 0.48) * price * 0.03
    const open = price
    const close = Math.round(price + change)
    const high = Math.round(Math.max(open, close) * (1 + Math.random() * 0.01))
    const low = Math.round(Math.min(open, close) * (1 - Math.random() * 0.01))
    price = close

    candles.push({
      time: date.toISOString().split('T')[0],
      open,
      high,
      low,
      close,
      volume: Math.round(Math.random() * 2000000 + 500000),
    })
  }
  return candles
}

export const MOCK_CANDLES: Candle[] = generateCandles(73000, 120)

export const MOCK_STOCK_DETAILS: Record<string, StockDetail> = {
  '005930': { open: 72800, high: 74200, low: 72100, volume: 12300000 },
  '000660': { open: 184000, high: 186500, low: 183500, volume: 5200000 },
  '035420': { open: 209000, high: 211500, low: 208500, volume: 3100000 },
  '035720': { open: 41800, high: 42500, low: 41600, volume: 8700000 },
  '051910': { open: 318000, high: 322000, low: 317000, volume: 1200000 },
}

export const MOCK_AI_SIGNAL = {
  signal: 'BUY' as const,
  signal_score: 78,
  tech_score: 72,
  lstm_score: 84,
  confidence: 0.81,
  indicators: {
    rsi_14: 62.4,
    macd: 12.3,
    macd_signal: 8.1,
    macd_hist: 4.2,
    bb_upper: 76200,
    bb_middle: 73400,
    bb_lower: 70600,
    ma5: 73200,
    ma20: 72100,
    ma60: 70500,
    ma120: 68900,
  },
}

export const MOCK_PREDICTION = {
  bullish: [74200, 75100, 76300, 77500, 78200],
  base:    [73800, 74300, 74900, 75400, 75800],
  bearish: [73200, 72800, 72100, 71500, 70900],
  confidence: 0.81,
}

export const MOCK_PATTERNS: CandlePattern[] = [
  { name: '망치형', type: 'bullish', description: '하락 추세 후 반전 가능성을 나타내는 강세 패턴' },
  { name: '도지', type: 'neutral', description: '시장 불확실성을 나타내며 추세 전환 신호일 수 있음' },
  { name: '상승장악형', type: 'bullish', description: '전일 하락을 완전히 상쇄하는 강한 매수 신호' },
]

export const MOCK_MULTIFRAME: MultiframeSignal[] = [
  { timeframe: '1D', signal: 'BUY', score: 78 },
  { timeframe: '1W', signal: 'HOLD', score: 52 },
  { timeframe: '1M', signal: 'BUY', score: 65 },
]

export const MOCK_ORDER_BOOK = {
  asks: [
    { price: 74200, quantity: 1200 },
    { price: 74100, quantity: 850 },
    { price: 74000, quantity: 2300 },
    { price: 73900, quantity: 600 },
    { price: 73800, quantity: 1800 },
    { price: 73700, quantity: 950 },
    { price: 73600, quantity: 3100 },
    { price: 73500, quantity: 720 },
    { price: 73450, quantity: 1500 },
    { price: 73420, quantity: 2800 },
  ] as OrderBookEntry[],
  bids: [
    { price: 73400, quantity: 4200 },
    { price: 73380, quantity: 1100 },
    { price: 73350, quantity: 2600 },
    { price: 73300, quantity: 800 },
    { price: 73250, quantity: 1900 },
    { price: 73200, quantity: 650 },
    { price: 73150, quantity: 3400 },
    { price: 73100, quantity: 1200 },
    { price: 73050, quantity: 2100 },
    { price: 73000, quantity: 900 },
  ] as OrderBookEntry[],
}

export const MOCK_HOLDINGS: Holding[] = [
  { stock_code: '005930', stock_name: '삼성전자', quantity: 10, avg_price: 70000, current_price: 73400, profit_loss: 34000, return_pct: 4.86, ai_signal: 'BUY' },
  { stock_code: '000660', stock_name: 'SK하이닉스', quantity: 5, avg_price: 180000, current_price: 185000, profit_loss: 25000, return_pct: 2.78, ai_signal: 'HOLD' },
  { stock_code: '035420', stock_name: 'NAVER', quantity: 3, avg_price: 220000, current_price: 210000, profit_loss: -30000, return_pct: -4.55, ai_signal: 'SELL' },
]

export const MOCK_PORTFOLIO_PERFORMANCE: { date: string; value: number }[] = Array.from({ length: 30 }, (_, i) => {
  const date = new Date('2026-05-01')
  date.setDate(date.getDate() + i)
  return {
    date: date.toISOString().split('T')[0],
    value: 5000000 + Math.round((Math.random() - 0.45) * 100000 * (i + 1)),
  }
})

export const MOCK_PORTFOLIO_METRICS: PortfolioMetrics = {
  total_value: 5290000,
  total_return_pct: 5.8,
  mdd: -3.2,
}

export const MOCK_BACKTEST_RESULT = {
  return_pct: 18.4,
  win_rate: 62.5,
  mdd: -7.3,
  trades: 24,
}
