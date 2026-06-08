// frontend/src/components/MainPanel/ChartTab/ChartTab.tsx
import { useStockStore } from '@/store/stockStore'
import { MOCK_CANDLES, MOCK_PREDICTION, MOCK_PATTERNS } from '@/lib/mockData'
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
import type { Candle, CandlePattern, Prediction, StockDetail } from '@/types'
import api from '@/lib/api'

function yyyymmddToIso(d: string): string {
  return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`
}

// 백엔드 패턴 영문명 → 한글명/설명 매핑 (pattern_service._PATTERNS와 일치).
const PATTERN_INFO: Record<string, { name: string; description: string }> = {
  hammer: { name: '망치형', description: '하락 추세 후 반전 가능성을 나타내는 강세 패턴' },
  invertedhammer: { name: '역망치형', description: '하락 추세 바닥에서 반등 가능성을 시사하는 패턴' },
  doji: { name: '도지', description: '시장 불확실성을 나타내며 추세 전환 신호일 수 있음' },
  engulfing: { name: '장악형', description: '전일 캔들을 완전히 감싸는 강한 추세 전환 신호' },
  morningstar: { name: '샛별형', description: '하락 추세 후 강한 상승 반전을 나타내는 패턴' },
  eveningstar: { name: '석별형', description: '상승 추세 후 하락 반전을 나타내는 패턴' },
  shootingstar: { name: '유성형', description: '상승 추세 고점에서 하락 반전을 시사하는 패턴' },
  hangingman: { name: '교수형', description: '상승 추세 고점에서 하락 전환 경고 신호' },
  '3whitesoldiers': { name: '적삼병', description: '연속 양봉으로 강한 상승 추세를 나타내는 패턴' },
  '3blackcrows': { name: '흑삼병', description: '연속 음봉으로 강한 하락 추세를 나타내는 패턴' },
  piercingline: { name: '관통형', description: '전일 음봉을 절반 이상 관통하는 강세 반전 패턴' },
  darkcloudcover: { name: '먹구름형', description: '전일 양봉을 절반 이상 덮는 약세 반전 패턴' },
  harami: { name: '잉태형', description: '전일 캔들 범위 안에 들어오는 추세 전환 신호' },
  haramicross: { name: '잉태십자형', description: '잉태형에 도지가 결합된 강한 전환 신호' },
}

interface PatternResponse {
  patterns?: { name: string; direction: string; value: number }[]
}

interface PredictResponse {
  prediction?: { bullish?: number[]; base?: number[]; bearish?: number[] }
  current_price?: number
  lstm_available?: boolean
}

export function ChartTab() {
  const { selectedStock, realtimePrice } = useStockStore()
  const { isConnected } = useStockWebSocket(selectedStock?.code ?? '')
  const [chart, setChart] = useState<IChartApi | null>(null)
  const [candles, setCandles] = useState<Candle[]>(MOCK_CANDLES)
  const [patterns, setPatterns] = useState<CandlePattern[]>(MOCK_PATTERNS)
  const [prediction, setPrediction] = useState<Prediction>(MOCK_PREDICTION)
  const [detail, setDetail] = useState<StockDetail | null>(null)

  useEffect(() => {
    if (!selectedStock?.code) return
    const code = selectedStock.code

    api.get(`/stocks/${code}/chart`).then(({ data }) => {
      const raw: { date: string; open: number; high: number; low: number; close: number; volume: number }[] = data.data ?? []
      if (raw.length === 0) return
      const mapped = raw.map((d) => ({
        time: d.date.length === 8 ? yyyymmddToIso(d.date) : d.date,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume,
      }))
      setCandles(mapped)
      const last = raw[raw.length - 1]
      if (last) setDetail({ open: last.open, high: last.high, low: last.low, volume: last.volume })
    }).catch(() => {})

    api.get<PatternResponse>(`/ai/${code}/patterns`).then(({ data }) => {
      const raw = data?.patterns ?? []
      if (raw.length === 0) return
      setPatterns(raw.map((p) => {
        const info = PATTERN_INFO[p.name]
        const type: CandlePattern['type'] =
          p.direction === 'bullish' ? 'bullish' : p.direction === 'bearish' ? 'bearish' : 'neutral'
        return {
          name: info?.name ?? p.name,
          type,
          description: info?.description ?? '',
        }
      }))
    }).catch(() => {})

    api.get<PredictResponse>(`/ai/${code}/predict`).then(({ data }) => {
      const p = data?.prediction
      if (!p) return
      const bullish = p.bullish ?? []
      const base = p.base ?? []
      const bearish = p.bearish ?? []
      // 학습 가중치가 없으면 빈 배열이 오므로 mock을 유지한다.
      if (bullish.length === 0 && base.length === 0 && bearish.length === 0) return
      setPrediction({ bullish, base, bearish, confidence: 0 })
    }).catch(() => {})
  }, [selectedStock?.code])

  const rsiData = useMemo(() => calculateRSI(candles), [candles])
  const macdData = useMemo(() => calculateMACD(candles), [candles])
  const lastCandleTime = candles[candles.length - 1]?.time ?? '2026-01-01'

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
      <PatternBadges patterns={patterns} />
      <div className="flex flex-col flex-1 min-h-0 gap-0.5 p-1">
        <div className="flex-[3] min-h-0">
          <CandleChart candles={candles} onChartReady={setChart} />
          <PredictionOverlay
            chart={chart}
            prediction={prediction}
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
