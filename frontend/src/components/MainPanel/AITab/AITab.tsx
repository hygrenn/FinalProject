import { useEffect, useState } from 'react'
import { useStockStore } from '@/store/stockStore'
import type { AISignal, MultiframeSignal } from '@/types'
import { MOCK_AI_SIGNAL, MOCK_MULTIFRAME } from '@/lib/mockData'
import api from '@/lib/api'
import { SignalCard } from './SignalCard'
import { ScoreBreakdown } from './ScoreBreakdown'
import { MultiframePanel } from './MultiframePanel'

// 백엔드 /ai/{code}/signal 응답 — signal_breakdown으로 점수를 감싸서 반환한다.
interface SignalResponse {
  signal: AISignal['signal']
  signal_score: number
  signal_breakdown?: {
    technical_score: number
    lstm_score: number
  }
  lstm_available?: boolean
}

// 백엔드 /ai/{code}/multiframe 응답 — timeframes 객체(daily/weekly/monthly).
interface MultiframeResponse {
  timeframes?: Record<string, { signal: MultiframeSignal['signal']; score: number }>
}

const TF_LABELS: [string, MultiframeSignal['timeframe']][] = [
  ['daily', '1D'],
  ['weekly', '1W'],
  ['monthly', '1M'],
]

export function AITab() {
  const selectedStock = useStockStore((s) => s.selectedStock)
  const [signal, setSignal] = useState<AISignal>(MOCK_AI_SIGNAL)
  const [multiframe, setMultiframe] = useState<MultiframeSignal[]>(MOCK_MULTIFRAME)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!selectedStock?.code) return
    const code = selectedStock.code
    const fetchData = async () => {
      setLoading(true)
      try {
        const [sigRes, mfRes] = await Promise.all([
          api.get<SignalResponse>(`/ai/${code}/signal`),
          api.get<MultiframeResponse>(`/ai/${code}/multiframe`),
        ])

        const sd = sigRes.data
        if (sd?.signal) {
          setSignal((prev) => ({
            ...prev,
            signal: sd.signal,
            signal_score: sd.signal_score,
            tech_score: sd.signal_breakdown?.technical_score ?? sd.signal_score,
            lstm_score: sd.signal_breakdown?.lstm_score ?? 50,
            // 백엔드는 별도 confidence를 주지 않으므로 중립(50)에서의 거리로 산출한다.
            confidence: Math.min(1, Math.abs(sd.signal_score - 50) / 50),
          }))
        }

        const tf = mfRes.data?.timeframes
        if (tf) {
          const frames = TF_LABELS.filter(([key]) => tf[key]).map(([key, label]) => ({
            timeframe: label,
            signal: tf[key].signal,
            score: tf[key].score,
          }))
          if (frames.length > 0) setMultiframe(frames)
        }
      } catch {
        // keep mock data on error
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [selectedStock?.code])

  const { signal: sig, signal_score, tech_score, lstm_score, confidence } = signal

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {loading && (
        <div className="text-xs text-muted-foreground text-center py-2">AI 분석 중...</div>
      )}
      <SignalCard
        signal={sig}
        signal_score={signal_score}
        confidence={confidence}
      />
      <ScoreBreakdown
        tech_score={tech_score}
        lstm_score={lstm_score}
        confidence={confidence}
      />
      <MultiframePanel signals={multiframe} />
    </div>
  )
}
