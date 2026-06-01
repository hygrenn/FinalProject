// frontend/src/types/index.ts
// 공동 관리 파일 — 수정 전 반드시 hygrenn과 협의 (CLAUDE.md §5)

export interface User {
  id: string
  email: string
  mode: 'demo' | 'paper' | 'real'
  access_allowed: boolean
  is_verified: boolean
  dark_mode: boolean
}

export interface AISignal {
  signal: 'BUY' | 'HOLD' | 'SELL'
  signal_score: number
  tech_score: number
  lstm_score: number
  confidence: number
  indicators: {
    rsi_14: number
    macd: number
    macd_signal: number
    macd_hist: number
    bb_upper: number
    bb_middle: number
    bb_lower: number
    ma5: number
    ma20: number
    ma60: number
    ma120: number
  }
}

export interface Prediction {
  bullish: number[]
  base: number[]
  bearish: number[]
  confidence: number
}

export interface Candle {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface Holding {
  stock_code: string
  stock_name: string
  quantity: number
  avg_price: number
  current_price: number
  profit_loss: number
  return_pct: number
  ai_signal: 'BUY' | 'HOLD' | 'SELL'
}

export interface OrderRequest {
  stock_code: string
  order_type: 'BUY' | 'SELL'
  price_type: 'MARKET' | 'LIMIT'
  quantity: number
  price?: number
  mode: 'paper' | 'real'
}

export interface LumpsumRequest {
  tickers: string[]
  buy_date: string
  sell_date: string
  amount_krw: number
}

export interface LumpsumResult {
  ticker: string
  name: string
  shares: number
  buy_price: number
  sell_price: number
  buy_value_krw: number
  sell_value_krw: number
  profit_krw: number
  return_pct: number
  chart_data: { date: string; return_pct: number }[]
}

export type TabId = 'chart' | 'ai' | 'simulator' | 'portfolio' | 'screener' | 'backtest'

export interface Stock {
  code: string
  name: string
  price?: number
  change_pct?: number
}
