// frontend/src/lib/mockData.ts
import type { Candle, Stock, StockDetail, CandlePattern, MultiframeSignal } from '@/types'

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
