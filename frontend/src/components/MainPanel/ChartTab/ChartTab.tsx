// frontend/src/components/MainPanel/ChartTab/ChartTab.tsx
import { useStockStore } from '@/store/stockStore'
import { MOCK_CANDLES, MOCK_STOCK_DETAILS, MOCK_PREDICTION, MOCK_PATTERNS } from '@/lib/mockData'
import { calculateRSI, calculateMACD } from '@/lib/indicators'
import { useStockWebSocket } from '@/hooks/useStockWebSocket'
import { StockInfoBar } from './StockInfoBar'
import { CandleChart } from './CandleChart'
import { PredictionOverlay } from './PredictionOverlay'
import { PatternBadges } from './PatternBadges'
import { RSIChart } from './RSIChart'
import { MACDChart } from './MACDChart'
import { useMemo, useState } from 'react'
import type { IChartApi } from 'lightweight-charts'

export function ChartTab() {
  const { selectedStock, realtimePrice } = useStockStore()
  const { isConnected } = useStockWebSocket(selectedStock?.code ?? '')
  const [chart, setChart] = useState<IChartApi | null>(null)

  const rsiData = useMemo(() => calculateRSI(MOCK_CANDLES), [])
  const macdData = useMemo(() => calculateMACD(MOCK_CANDLES), [])
  const lastCandleTime = MOCK_CANDLES[MOCK_CANDLES.length - 1]?.time ?? '2026-01-01'

  const stockCode = selectedStock?.code ?? '005930'
  const detail = MOCK_STOCK_DETAILS[stockCode] ?? MOCK_STOCK_DETAILS['005930']

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {selectedStock && (
        <StockInfoBar
          stock={selectedStock}
          detail={detail}
          isLive={isConnected}
          realtimePrice={realtimePrice?.price}
          realtimeChangePct={realtimePrice?.change_pct}
        />
      )}
      <PatternBadges patterns={MOCK_PATTERNS} />
      <div className="flex flex-col flex-1 min-h-0 gap-0.5 p-1">
        <div className="flex-[3] min-h-0">
          <CandleChart candles={MOCK_CANDLES} onChartReady={setChart} />
          <PredictionOverlay
            chart={chart}
            prediction={MOCK_PREDICTION}
            lastCandleTime={lastCandleTime}
          />
        </div>
        <div className="flex-1 min-h-0">
          <RSIChart data={rsiData} />
        </div>
        <div className="flex-1 min-h-0">
          <MACDChart data={macdData} />
        </div>
      </div>
    </div>
  )
}
