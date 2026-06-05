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
import { useMemo, useState, useEffect } from 'react'
import type { IChartApi } from 'lightweight-charts'
import type { Candle } from '@/types'
import api from '@/lib/api'

function yyyymmddToIso(d: string): string {
  return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`
}

export function ChartTab() {
  const { selectedStock, realtimePrice } = useStockStore()
  const { isConnected } = useStockWebSocket(selectedStock?.code ?? '')
  const [chart, setChart] = useState<IChartApi | null>(null)
  const [candles, setCandles] = useState<Candle[]>(MOCK_CANDLES)

  useEffect(() => {
    if (!selectedStock?.code) return
    api.get(`/stocks/${selectedStock.code}/chart`).then(({ data }) => {
      const raw: { date: string; open: number; high: number; low: number; close: number; volume: number }[] = data.data ?? []
      if (raw.length === 0) return
      setCandles(raw.map((d) => ({
        time: d.date.length === 8 ? yyyymmddToIso(d.date) : d.date,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume,
      })))
    }).catch(() => {})
  }, [selectedStock?.code])

  const rsiData = useMemo(() => calculateRSI(candles), [candles])
  const macdData = useMemo(() => calculateMACD(candles), [candles])
  const lastCandleTime = candles[candles.length - 1]?.time ?? '2026-01-01'

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
          <CandleChart candles={candles} onChartReady={setChart} />
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
