import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { MOCK_STOCKS, MOCK_CANDLES } from '@/lib/mockData'
import { cn } from '@/lib/utils'

export function SimulatorTab() {
  const [buyDate, setBuyDate] = useState('2026-01-02')
  const [sellDate, setSellDate] = useState('2026-03-01')
  const [amount, setAmount] = useState('1000000')
  const [result, setResult] = useState<{ profit: number; returnPct: number } | null>(null)

  const handleSimulate = (e: React.FormEvent) => {
    e.preventDefault()
    const buyCandle = MOCK_CANDLES.find((c) => c.time >= buyDate)
    const sellCandle = [...MOCK_CANDLES].reverse().find((c) => c.time <= sellDate)
    if (!buyCandle || !sellCandle) return

    const shares = Math.floor(Number(amount) / buyCandle.close)
    const profit = shares * (sellCandle.close - buyCandle.close)
    const returnPct = ((sellCandle.close - buyCandle.close) / buyCandle.close) * 100
    setResult({ profit, returnPct })
  }

  return (
    <div className="h-full overflow-y-auto p-4">
      <h2 className="text-base font-semibold mb-4">투자 시뮬레이터</h2>

      <form onSubmit={handleSimulate} className="space-y-3 bg-card border border-border rounded-lg p-4">
        <div>
          <label className="text-xs text-muted-foreground">종목</label>
          <div className="mt-1 text-sm font-medium">{MOCK_STOCKS[0].name} (삼성전자)</div>
        </div>
        <div>
          <label className="text-xs text-muted-foreground">매수일</label>
          <Input type="date" value={buyDate} onChange={(e) => setBuyDate(e.target.value)} className="mt-1" />
        </div>
        <div>
          <label className="text-xs text-muted-foreground">매도일</label>
          <Input type="date" value={sellDate} onChange={(e) => setSellDate(e.target.value)} className="mt-1" />
        </div>
        <div>
          <label className="text-xs text-muted-foreground">투자금액</label>
          <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} className="mt-1" />
        </div>
        <Button type="submit" className="w-full">시뮬레이션 실행</Button>
      </form>

      {result && (
        <div className="mt-4 bg-card border border-border rounded-lg p-4 space-y-2">
          <div className="text-sm font-semibold">시뮬레이션 결과</div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">수익/손실</span>
            <span className={cn('font-medium', result.profit >= 0 ? 'text-green-400' : 'text-red-400')}>
              {result.profit >= 0 ? '+' : ''}{result.profit.toLocaleString()}원
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">수익률</span>
            <span className={cn('font-medium', result.returnPct >= 0 ? 'text-green-400' : 'text-red-400')}>
              {result.returnPct >= 0 ? '+' : ''}{result.returnPct.toFixed(2)}%
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
