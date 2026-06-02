// frontend/src/components/MainPanel/MainPanel.tsx
import { useUIStore } from '@/store/uiStore'
import { ChartTab } from './ChartTab/ChartTab'
import { AITab } from './AITab/AITab'
import { cn } from '@/lib/utils'
import type { TabId } from '@/types'

const ALL_TABS: { id: TabId; label: string }[] = [
  { id: 'chart', label: '차트' },
  { id: 'ai', label: 'AI' },
  { id: 'simulator', label: '시뮬' },
  { id: 'portfolio', label: '포트폴리오' },
  { id: 'screener', label: '스크리너' },
  { id: 'backtest', label: '백테스트' },
]

const PLACEHOLDER_TABS = ['simulator', 'portfolio', 'screener', 'backtest'] as const

function PlaceholderTab({ name }: { name: string }) {
  return (
    <div className="flex items-center justify-center h-full text-muted-foreground">
      {name} — Phase 4에서 구현 예정
    </div>
  )
}

export function MainPanel() {
  const { activeTab, setActiveTab } = useUIStore()

  return (
    <div className="flex-1 min-w-0 min-h-0 overflow-hidden flex flex-col">
      {/* 데스크탑 탭 헤더 (모바일에서는 숨김) */}
      <div className="hidden md:flex border-b border-border bg-card shrink-0 overflow-x-auto">
        {ALL_TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'px-4 h-9 text-sm whitespace-nowrap shrink-0 border-b-2 transition-colors',
              activeTab === tab.id
                ? 'border-primary text-foreground font-medium'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="flex-1 min-h-0 overflow-hidden">
        {activeTab === 'chart' && <ChartTab />}
        {activeTab === 'ai' && <AITab />}
        {PLACEHOLDER_TABS.map((tab) =>
          activeTab === tab ? <PlaceholderTab key={tab} name={tab} /> : null
        )}
      </div>
    </div>
  )
}
