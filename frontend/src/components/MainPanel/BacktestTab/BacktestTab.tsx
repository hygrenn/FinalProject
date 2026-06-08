import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { useStockStore } from '@/store/stockStore'
import api from '@/lib/api'

interface BacktestResultData {
  total_return_pct: number
  win_rate_pct: number
  mdd_pct: number
  total_trades: number
  sharpe_ratio: number
}

export function BacktestTab() {
  const selectedStock = useStockStore((s) => s.selectedStock)
  const [startDate, setStartDate] = useState('2025-01-02')
  const [endDate, setEndDate] = useState('2026-01-01')
  const [initialCash, setInitialCash] = useState('10000000')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BacktestResultData | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedStock?.code) return
    setError(null)
    setLoading(true)
    try {
      const { data } = await api.post('/backtest/run', {
        code: selectedStock.code,
        start_date: startDate,
        end_date: endDate,
        initial_cash: Number(initialCash),
      })
      setResult(data)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? '백테스트 실행 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-4">
      <h2 className="text-base font-semibold mb-4">백테스팅</h2>
      {selectedStock && (
        <div className="text-xs text-muted-foreground mb-3">
          종목: <span className="text-foreground font-medium">{selectedStock.name} ({selectedStock.code})</span>
        </div>
      )}

      <form onSubmit={handleRun} className="space-y-3 bg-card border border-border rounded-lg p-4">
        <div>
          <label className="text-xs text-muted-foreground">시작일</label>
          <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="mt-1" />
        </div>
        <div>
          <label className="text-xs text-muted-foreground">종료일</label>
          <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="mt-1" />
        </div>
        <div>
          <label className="text-xs text-muted-foreground">초기 자본 (원)</label>
          <Input type="number" value={initialCash} onChange={(e) => setInitialCash(e.target.value)} className="mt-1" />
        </div>
        {error && <div className="text-xs text-red-400">{error}</div>}
        <Button type="submit" className="w-full" disabled={loading || !selectedStock}>
          {loading ? '실행 중...' : '백테스트 실행'}
        </Button>
      </form>

      {result && (
        <div className="mt-4 bg-card border border-border rounded-lg p-4">
          <div className="text-sm font-semibold mb-3">결과</div>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: '수익률', value: `${result.total_return_pct >= 0 ? '+' : ''}${result.total_return_pct.toFixed(2)}%`, positive: result.total_return_pct >= 0 },
              { label: '승률', value: `${result.win_rate_pct.toFixed(1)}%`, positive: true },
              { label: 'MDD', value: `-${result.mdd_pct.toFixed(1)}%`, positive: false },
              { label: '거래 횟수', value: `${result.total_trades}회`, positive: null },
              { label: '샤프비율', value: result.sharpe_ratio.toFixed(2), positive: result.sharpe_ratio > 0 },
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
