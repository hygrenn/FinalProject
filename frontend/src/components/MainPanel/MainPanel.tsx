// frontend/src/components/MainPanel/MainPanel.tsx
import { useUIStore } from '@/store/uiStore'
import { ChartTab } from './ChartTab/ChartTab'
import { AITab } from './AITab/AITab'

const PLACEHOLDER_TABS = ['simulator', 'portfolio', 'screener', 'backtest'] as const

function PlaceholderTab({ name }: { name: string }) {
  return (
    <div className="flex items-center justify-center h-full text-muted-foreground">
      {name} — Phase 4에서 구현 예정
    </div>
  )
}

export function MainPanel() {
  const { activeTab } = useUIStore()

  return (
    <div className="flex-1 min-w-0 min-h-0 overflow-hidden">
      {activeTab === 'chart' && <ChartTab />}
      {activeTab === 'ai' && <AITab />}
      {PLACEHOLDER_TABS.map((tab) =>
        activeTab === tab ? <PlaceholderTab key={tab} name={tab} /> : null
      )}
    </div>
  )
}
