import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface RiskSettingsModalProps {
  open: boolean
  onClose: () => void
}

export function RiskSettingsModal({ open, onClose }: RiskSettingsModalProps) {
  const [maxPosition, setMaxPosition] = useState('20')
  const [stopLoss, setStopLoss] = useState('5')
  const [dailyLimit, setDailyLimit] = useState('500000')

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>리스크 설정</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSave} className="space-y-3">
          <div>
            <label className="text-xs text-muted-foreground">1회 최대 투자 비중 (%)</label>
            <Input type="number" value={maxPosition} onChange={(e) => setMaxPosition(e.target.value)} className="mt-1" min="1" max="100" />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">손절 기준 (%)</label>
            <Input type="number" value={stopLoss} onChange={(e) => setStopLoss(e.target.value)} className="mt-1" min="1" max="50" />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">일일 최대 손실 한도 (원)</label>
            <Input type="number" value={dailyLimit} onChange={(e) => setDailyLimit(e.target.value)} className="mt-1" />
          </div>
          <Button type="submit" className="w-full">저장</Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
