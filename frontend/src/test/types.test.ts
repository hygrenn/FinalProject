import type { User, Candle, TabId, StockDetail } from '@/types'

describe('types', () => {
  it('User type has required fields', () => {
    const user: User = {
      id: '1',
      email: 'test@test.com',
      mode: 'demo',
      access_allowed: true,
      is_verified: true,
      dark_mode: true,
    }
    expect(user.mode).toBe('demo')
  })

  it('Candle type has OHLCV fields', () => {
    const candle: Candle = {
      time: '2026-06-01',
      open: 73000,
      high: 74000,
      low: 72500,
      close: 73400,
      volume: 1000000,
    }
    expect(candle.close).toBe(73400)
  })

  it('TabId covers all tabs', () => {
    const tabs: TabId[] = ['chart', 'ai', 'simulator', 'portfolio', 'screener', 'backtest']
    expect(tabs).toHaveLength(6)
  })

  it('StockDetail has OHLV fields', () => {
    const detail: StockDetail = { open: 72800, high: 74200, low: 72100, volume: 12300000 }
    expect(detail.high).toBe(74200)
  })
})
