import { useEffect, useState } from 'react'
import { useStockStore } from '@/store/stockStore'
import api from '@/lib/api'

// 백엔드 /analysis/recommendations 응답
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
  scanned: number
  buy_count: number
  market_trend: string
  market_caution: boolean
}

export function RecommendationPanel() {
  const setSelectedStock = useStockStore((s) => s.setSelectedStock)
  const [data, setData] = useState<RecommendationResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const load = () => {
    setLoading(true)
    api.get<RecommendationResponse>('/analysis/recommendations', { params: { limit: 15 } })
      .then(({ data }) => setData(data))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

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
          {data.scanned}종목 스캔 · BUY {data.buy_count}개
          {data.market_caution && <span className="text-red-400"> · ⚠ 시장 하락 주의</span>}
        </div>
      )}

      {loading && <div className="text-xs text-muted-foreground py-3 text-center">100종목 스캔 중…</div>}

      {!loading && data && data.picks.length === 0 && (
        <div className="text-xs text-muted-foreground py-3 text-center">현재 BUY 추천 종목이 없습니다.</div>
      )}

      {!loading && data && data.picks.length > 0 && (
        <ul className="space-y-1">
          {data.picks.map((p) => (
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
                <div className="text-xs font-semibold text-green-400">BUY {p.signal_score.toFixed(0)}</div>
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
