import { MOCK_HOLDINGS, MOCK_PORTFOLIO_METRICS, MOCK_PORTFOLIO_PERFORMANCE } from '@/lib/mockData'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { cn } from '@/lib/utils'

export function PortfolioTab() {
  const { total_value, total_return_pct, mdd } = MOCK_PORTFOLIO_METRICS

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {/* 요약 카드 */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-card border border-border rounded-lg p-3 text-center">
          <div className="text-xs text-muted-foreground mb-1">총 평가액</div>
          <div className="text-sm font-bold">{(total_value / 10000).toFixed(0)}만원</div>
        </div>
        <div className="bg-card border border-border rounded-lg p-3 text-center">
          <div className="text-xs text-muted-foreground mb-1">수익률</div>
          <div className={cn('text-sm font-bold', total_return_pct >= 0 ? 'text-green-400' : 'text-red-400')}>
            {total_return_pct >= 0 ? '+' : ''}{total_return_pct.toFixed(1)}%
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-3 text-center">
          <div className="text-xs text-muted-foreground mb-1">MDD</div>
          <div className="text-sm font-bold text-red-400">{mdd.toFixed(1)}%</div>
        </div>
      </div>

      {/* 수익률 차트 */}
      <div className="bg-card border border-border rounded-lg p-3">
        <div className="text-sm font-semibold mb-3">평가금액 추이</div>
        <ResponsiveContainer width="100%" height={140}>
          <LineChart data={MOCK_PORTFOLIO_PERFORMANCE}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} tickFormatter={(v) => v.slice(5)} />
            <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} tickFormatter={(v) => `${(v / 10000).toFixed(0)}만`} />
            <Tooltip
              formatter={(v: number) => [`${v.toLocaleString()}원`, '평가금액']}
              contentStyle={{ background: '#161b22', border: '1px solid #30363d', fontSize: 11 }}
            />
            <Line type="monotone" dataKey="value" stroke="#58a6ff" dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 보유종목 */}
      <div className="bg-card border border-border rounded-lg p-3">
        <div className="text-sm font-semibold mb-3">보유종목</div>
        <div className="space-y-2">
          {MOCK_HOLDINGS.map((h) => (
            <div key={h.stock_code} className="flex items-center justify-between text-sm py-1.5 border-b border-border last:border-0">
              <div>
                <div className="font-medium">{h.stock_name}</div>
                <div className="text-xs text-muted-foreground">{h.quantity}주 · 평균 {h.avg_price.toLocaleString()}원</div>
              </div>
              <div className="text-right">
                <div>{h.current_price.toLocaleString()}원</div>
                <div className={cn('text-xs', h.return_pct >= 0 ? 'text-green-400' : 'text-red-400')}>
                  {h.return_pct >= 0 ? '+' : ''}{h.return_pct.toFixed(2)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
