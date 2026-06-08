import { useEffect, useState } from 'react'
import { useStockStore } from '@/store/stockStore'
import type { AISignal, MultiframeSignal } from '@/types'
import { MOCK_AI_SIGNAL, MOCK_MULTIFRAME } from '@/lib/mockData'
import api from '@/lib/api'
import { SignalCard } from './SignalCard'
import { ScoreBreakdown } from './ScoreBreakdown'
import { MultiframePanel } from './MultiframePanel'

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
          api.get(`/ai/${code}/signal`),
          api.get(`/ai/${code}/multiframe`),
        ])
        if (sigRes.data) setSignal(sigRes.data)
        if (mfRes.data?.signals) setMultiframe(mfRes.data.signals)
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
