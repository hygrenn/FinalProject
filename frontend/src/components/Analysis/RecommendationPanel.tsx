import { useEffect, useState } from 'react'
import { useStockStore } from '@/store/stockStore'
import api from '@/lib/api'

interface Pick {
  code: string
  name: string
  signal: string
  signal_score: number
  financial_score: number | null
  financial_grade: string | null
  market_caution: boolean
}

interface RecommendationResponse {
  picks: Pick[]
  sell_warnings: Pick[]
  scanned: number
  buy_count: number
  sell_count: number
  market_trend: string
  market_caution: boolean
}

export function RecommendationPanel() {
  const setSelectedStock = useStockStore((s) => s.setSelectedStock)
  const [data, setData] = useState<RecommendationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<'buy' | 'sell'>('buy')

  const load = () => {
    setLoading(true)
    api.get<RecommendationResponse>('/analysis/recommendations', { params: { limit: 15 } })
      .then(({ data }) => setData(data))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const buyList = data?.picks ?? []
  const sellList = data?.sell_warnings ?? []

  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold">AI 추천 종목</h3>
        <button
          onClick={load}
          className="text-[11px] text-muted-foreground hover:text-foreground border border-border rounded px-1.5 py-0.5"
        >
          새로고침
        </button>
      </div>

      {data && (
        <div className="text-[11px] text-muted-foreground mb-2">
          {data.scanned}종목 스캔 · BUY {data.buy_count}개 · SELL {data.sell_count}개
          {data.market_caution && <span className="text-red-400"> · ⚠ 시장 하락 주의</span>}
        </div>
      )}

      {/* BUY / SELL 탭 */}
      <div className="flex gap-1 mb-2">
        <button
          onClick={() => setTab('buy')}
          className={`flex-1 text-[11px] py-0.5 rounded transition-colors ${
            tab === 'buy'
              ? 'bg-green-500/20 text-green-400 border border-green-500/30'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          매수 추천 {data ? `(${data.buy_count})` : ''}
        </button>
        <button
          onClick={() => setTab('sell')}
          className={`flex-1 text-[11px] py-0.5 rounded transition-colors ${
            tab === 'sell'
              ? 'bg-red-500/20 text-red-400 border border-red-500/30'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          매도 경고 {data ? `(${data.sell_count})` : ''}
        </button>
      </div>

      {loading && <div className="text-xs text-muted-foreground py-3 text-center">100종목 스캔 중…</div>}

      {!loading && tab === 'buy' && buyList.length === 0 && (
        <div className="text-xs text-muted-foreground py-3 text-center">현재 BUY 추천 종목이 없습니다.</div>
      )}
      {!loading && tab === 'sell' && sellList.length === 0 && (
        <div className="text-xs text-muted-foreground py-3 text-center">현재 SELL 경고 종목이 없습니다.</div>
      )}

      {!loading && (
        <ul className="space-y-1">
          {(tab === 'buy' ? buyList : sellList).map((p) => (
            <li
              key={p.code}
              onClick={() => setSelectedStock({ code: p.code, name: p.name })}
              className="flex items-center justify-between cursor-pointer rounded px-2 py-1.5 hover:bg-accent"
            >
              <div className="min-w-0">
                <div className="text-sm font-medium truncate">{p.name}</div>
                <div className="text-[11px] text-muted-foreground">{p.code}</div>
              </div>
              <div className="text-right shrink-0 ml-2">
                {tab === 'buy' ? (
                  <div className="text-xs font-semibold text-green-400">BUY {p.signal_score.toFixed(0)}</div>
                ) : (
                  <div className="text-xs font-semibold text-red-400">SELL {p.signal_score.toFixed(0)}</div>
                )}
                {p.financial_score != null && (
                  <div className="text-[11px] text-muted-foreground">재무 {p.financial_score.toFixed(1)}</div>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
