import { render, screen, fireEvent } from '@testing-library/react'
import { OrderModal } from '@/components/Trade/OrderModal'
import { MOCK_STOCKS } from '@/lib/mockData'

const stock = MOCK_STOCKS[0]

describe('OrderModal', () => {
  it('renders BUY modal title', () => {
    render(<OrderModal open={true} onClose={() => {}} stock={stock} orderType="BUY" />)
    expect(screen.getByText(/매수/)).toBeInTheDocument()
  })

  it('renders SELL modal title', () => {
    render(<OrderModal open={true} onClose={() => {}} stock={stock} orderType="SELL" />)
    expect(screen.getByText(/매도/)).toBeInTheDocument()
  })

  it('renders stock name', () => {
    render(<OrderModal open={true} onClose={() => {}} stock={stock} orderType="BUY" />)
    expect(screen.getByText('삼성전자')).toBeInTheDocument()
  })

  it('calls onClose when cancelled', () => {
    const fn = vi.fn()
    render(<OrderModal open={true} onClose={fn} stock={stock} orderType="BUY" />)
    fireEvent.click(screen.getByText('취소'))
    expect(fn).toHaveBeenCalled()
  })
})
