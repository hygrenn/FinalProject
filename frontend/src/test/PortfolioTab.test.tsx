import { render, screen } from '@testing-library/react'
import { PortfolioTab } from '@/components/MainPanel/PortfolioTab/PortfolioTab'

describe('PortfolioTab', () => {
  it('renders 총 평가액', () => {
    render(<PortfolioTab />)
    expect(screen.getByText('총 평가액')).toBeInTheDocument()
  })

  it('renders 보유종목 heading', () => {
    render(<PortfolioTab />)
    expect(screen.getByText('보유종목')).toBeInTheDocument()
  })

  it('renders holding stock names', () => {
    render(<PortfolioTab />)
    expect(screen.getByText('삼성전자')).toBeInTheDocument()
  })
})
