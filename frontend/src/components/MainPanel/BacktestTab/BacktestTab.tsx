import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { MOCK_BACKTEST_RESULT } from '@/lib/mockData'
import { cn } from '@/lib/utils'

export function BacktestTab() {
  const [startDate, setStartDate] = useState('2026-01-02')
  const [endDate, setEndDate] = useState('2026-04-01')
  const [strategy, setStrategy] = useState('MA교차')
  const [ran, setRan] = useState(false)

  const handleRun = (e: React.FormEvent) => {
    e.preventDefault()
    setRan(true)
  }

  return (
    <div className="h-full overflow-y-auto p-4">
      <h2 className="text-base font-semibold mb-4">백테스팅</h2>

      <form onSubmit={handleRun} className="space-y-3 bg-card border border-border rounded-lg p-4">
        <div>
          <label className="text-xs text-muted-foreground">전략</label>
          <div className="flex gap-2 mt-1">
            {['MA교차', 'RSI'].map((s) => (
              <Button key={s} type="button" size="sm" variant={strategy === s ? 'default' : 'outline'} onClick={() => setStrategy(s)}>
                {s}
              </Button>
            ))}
          </div>
        </div>
        <div>
          <label className="text-xs text-muted-foreground">시작일</label>
          <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="mt-1" />
        </div>
        <div>
          <label className="text-xs text-muted-foreground">종료일</label>
          <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="mt-1" />
        </div>
        <Button type="submit" className="w-full">백테스트 실행</Button>
      </form>

      {ran && (
        <div className="mt-4 bg-card border border-border rounded-lg p-4">
          <div className="text-sm font-semibold mb-3">결과 ({strategy})</div>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: '수익률', value: `+${MOCK_BACKTEST_RESULT.return_pct}%`, positive: true },
              { label: '승률', value: `${MOCK_BACKTEST_RESULT.win_rate}%`, positive: true },
              { label: 'MDD', value: `-${MOCK_BACKTEST_RESULT.mdd}%`, positive: false },
              { label: '거래 횟수', value: `${MOCK_BACKTEST_RESULT.trades}회`, positive: null },
            ].map(({ label, value, positive }) => (
              <div key={label} className="bg-background border border-border rounded p-2.5 text-center">
                <div className="text-xs text-muted-foreground mb-1">{label}</div>
                <div className={cn('text-sm font-bold',
                  positive === true ? 'text-green-400' : positive === false ? 'text-red-400' : 'text-foreground'
                )}>
                  {value}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
