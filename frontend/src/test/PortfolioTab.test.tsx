import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { PortfolioTab } from '@/components/MainPanel/PortfolioTab/PortfolioTab'

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn((url: string) => {
      if (url === '/portfolio') return Promise.resolve({ data: {
        holdings: [{ stock_code: '005930', stock_name: '삼성전자', quantity: 10, avg_price: 70000, current_price: 73400, eval_amount: 734000, profit_loss: 34000, return_pct: 4.86 }],
        total_eval: 5290000,
        total_cost: 5000000,
        total_return_pct: 5.8,
      }})
      if (url === '/portfolio/metrics') return Promise.resolve({ data: { total_trades: 24, win_rate_pct: 62.5, sharpe_ratio: 1.23, mdd_pct: 3.2 } })
      if (url === '/portfolio/performance') return Promise.resolve({ data: [] })
      return Promise.resolve({ data: {} })
    }),
  },
}))

describe('PortfolioTab', () => {
  it('renders 총 평가액', async () => {
    render(<PortfolioTab />)
    await waitFor(() => expect(screen.getByText('총 평가액')).toBeInTheDocument())
  })

  it('renders 보유종목 heading', async () => {
    render(<PortfolioTab />)
    await waitFor(() => expect(screen.getByText('보유종목')).toBeInTheDocument())
  })

  it('renders holding stock names', async () => {
    render(<PortfolioTab />)
    await waitFor(() => expect(screen.getByText('삼성전자')).toBeInTheDocument())
  })
})
