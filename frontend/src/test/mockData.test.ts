import { MOCK_STOCKS, MOCK_CANDLES, MOCK_WATCHLIST } from '@/lib/mockData'

describe('mockData', () => {
  it('MOCK_STOCKS has at least 5 items', () => {
    expect(MOCK_STOCKS.length).toBeGreaterThanOrEqual(5)
  })

  it('MOCK_CANDLES are in ascending date order', () => {
    for (let i = 1; i < MOCK_CANDLES.length; i++) {
      expect(MOCK_CANDLES[i].time > MOCK_CANDLES[i - 1].time).toBe(true)
    }
  })

  it('MOCK_WATCHLIST contains valid stock codes', () => {
    const codes = MOCK_STOCKS.map((s) => s.code)
    MOCK_WATCHLIST.forEach((code) => {
      expect(codes).toContain(code)
    })
  })
})
