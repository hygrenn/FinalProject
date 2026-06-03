import { render, screen, fireEvent } from '@testing-library/react'
import { RiskSettingsModal } from '@/components/Risk/RiskSettingsModal'

describe('RiskSettingsModal', () => {
  it('renders when open', () => {
    render(<RiskSettingsModal open={true} onClose={() => {}} />)
    expect(screen.getByText('리스크 설정')).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(<RiskSettingsModal open={false} onClose={() => {}} />)
    expect(screen.queryByText('리스크 설정')).not.toBeInTheDocument()
  })

  it('calls onClose when saved', () => {
    const fn = vi.fn()
    render(<RiskSettingsModal open={true} onClose={fn} />)
    fireEvent.click(screen.getByText('저장'))
    expect(fn).toHaveBeenCalled()
  })
})
