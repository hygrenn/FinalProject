import { render, screen, waitFor } from '@testing-library/react'
import { AccountPanel } from '@/components/Account/AccountPanel'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

vi.mock('@/lib/api', () => ({
  default: { get: vi.fn() },
}))

describe('AccountPanel', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: { id: '1', email: 'user@test.com', mode: 'demo', is_verified: true, dark_mode: true },
    })
    vi.mocked(api.get).mockResolvedValue({
      data: {
        mode: 'real',
        account_no: '1234****-01',
        summary: {
          total_asset: 1000000,
          deposit: 200000,
          eval_amount: 800000,
          buy_amount: 700000,
          eval_profit_loss: 100000,
          return_pct: 14.29,
        },
        holdings: [],
        data_source: 'KIS 실계좌 계좌',
      },
    })
  })

  it('loads the configured account without a query mode and shows real account warning', async () => {
    render(<AccountPanel onClose={() => {}} />)

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/account/balance'))
    expect(await screen.findByText('실계좌')).toBeInTheDocument()
    expect(screen.getByText('실제 주문이 이 계좌로 실행됩니다.')).toBeInTheDocument()
  })
})
