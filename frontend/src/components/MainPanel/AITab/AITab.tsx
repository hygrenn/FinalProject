import { MOCK_AI_SIGNAL, MOCK_MULTIFRAME } from '@/lib/mockData'
import { SignalCard } from './SignalCard'
import { ScoreBreakdown } from './ScoreBreakdown'
import { MultiframePanel } from './MultiframePanel'

export function AITab() {
  const { signal, signal_score, tech_score, lstm_score, confidence } = MOCK_AI_SIGNAL

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      <SignalCard
        signal={signal}
        signal_score={signal_score}
        confidence={confidence}
      />
      <ScoreBreakdown
        tech_score={tech_score}
        lstm_score={lstm_score}
        confidence={confidence}
      />
      <MultiframePanel signals={MOCK_MULTIFRAME} />
    </div>
  )
}
