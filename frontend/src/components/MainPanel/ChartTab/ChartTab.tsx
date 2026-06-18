// frontend/src/components/MainPanel/ChartTab/ChartTab.tsx
import { useStockStore } from '@/store/stockStore'
import { MOCK_CANDLES, MOCK_PATTERNS } from '@/lib/mockData'
import { calculateRSI, calculateMACD } from '@/lib/indicators'
import { useStockWebSocket } from '@/hooks/useStockWebSocket'
import { StockInfoBar } from './StockInfoBar'
import { CandleChart } from './CandleChart'
import { PredictionOverlay } from './PredictionOverlay'
import { SupportResistanceOverlay } from './SupportResistanceOverlay'
import { TrendlineOverlay } from './TrendlineOverlay'
import { AnomalyChart } from './AnomalyChart'
import { PatternBadges } from './PatternBadges'
import { RSIChart } from './RSIChart'
import { MACDChart } from './MACDChart'
import { cn } from '@/lib/utils'
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

// ─── AI 분석 타입 ─────────────────────────────────────────────────────────────

interface SRLevel { price: number; strength: number }
interface SRData  { support: SRLevel[]; resistance: SRLevel[] }

interface TrendPoint { date: string; price: number }
interface TrendLine  { label: string; color: string; r2: number; points: TrendPoint[]; pivots: TrendPoint[] }
interface TrendlineData { lines: TrendLine[]; available: boolean }

interface AnomalyScore  { date: string; score: number }
interface AnomalyData   { scores: AnomalyScore[]; threshold: number; available: boolean }

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
  const [prediction, setPrediction] = useState<Prediction>({ bullish: [], base: [], bearish: [], confidence: 0 })
  const [detail, setDetail] = useState<StockDetail | null>(null)
  const [interval, setInterval] = useState('day')
  const [period, setPeriod] = useState('1y')
  const [loadingIntraday, setLoadingIntraday] = useState(false)

  // AI 분석 오버레이 상태
  const [srData, setSrData]           = useState<SRData | null>(null)
  const [trendlineData, setTrendlineData] = useState<TrendlineData | null>(null)
  const [anomalyData, setAnomalyData] = useState<AnomalyData | null>(null)
  const [showSR, setShowSR]           = useState(true)
  const [showTrend, setShowTrend]     = useState(true)
  const [showAnomaly, setShowAnomaly] = useState(false)

  useEffect(() => {
    if (!selectedStock?.code) return
    const code = selectedStock.code

    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | undefined
    const fetchChart = async () => {
      try {
        const { data } = await api.get(`/stocks/${code}/chart`, { params: { interval, period } })
        if (cancelled) return
        const raw: { date: string | number; open: number; high: number; low: number; close: number; volume: number }[] = data.data ?? []
        if (raw.length > 0) {
          const mapped = raw.map((d) => ({
            time: typeof d.date === 'number'
              ? d.date
              : (String(d.date).length === 8 ? yyyymmddToIso(String(d.date)) : String(d.date)),
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
            volume: d.volume,
          }))
          setCandles(mapped)
          const last = raw[raw.length - 1]
          if (last) setDetail({ open: last.open, high: last.high, low: last.low, volume: last.volume })
        }
        const isLoading = data.status === 'loading_intraday'
        setLoadingIntraday(isLoading)
        if (isLoading) timer = setTimeout(fetchChart, 3000)
      } catch {
        setLoadingIntraday(false)
      }
    }
    fetchChart()

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

    // AI 분석 3종 병렬 요청
    Promise.all([
      api.get<SRData>(`/analysis/support-resistance/${code}`).catch(() => null),
      api.get<TrendlineData>(`/analysis/trendline/${code}`).catch(() => null),
      api.get<AnomalyData>(`/analysis/anomaly/${code}`).catch(() => null),
    ]).then(([sr, tl, an]) => {
      if (cancelled) return
      if (sr)  setSrData(sr.data)
      if (tl)  setTrendlineData(tl.data)
      if (an)  setAnomalyData(an.data)
    })

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
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [selectedStock?.code, interval, period])

  const INTRADAY = new Set(['1min', '5min', '15min', '1h'])
  const rsiData = useMemo(() => calculateRSI(candles), [candles])
  const macdData = useMemo(() => calculateMACD(candles), [candles])
  const lastCandleRaw = candles[candles.length - 1]?.time
  const lastCandleTime = typeof lastCandleRaw === 'number'
    ? new Date(lastCandleRaw * 1000).toISOString().slice(0, 10)
    : (lastCandleRaw ?? '2026-01-01')

  const INTERVALS = [
    { key: '1min', label: '1분' },
    { key: '5min', label: '5분' },
    { key: '1h',   label: '1시간' },
    { key: 'day',  label: '일' },
    { key: 'week', label: '주' },
    { key: 'month',label: '월' },
  ]

  const PERIODS = [
    { key: '1m',  label: '1개월' },
    { key: '3m',  label: '3개월' },
    { key: '1y',  label: '1년' },
    { key: '2y',  label: '2년' },
    { key: '3y',  label: '3년' },
    { key: '5y',  label: '5년' },
  ]

  const showPeriodBar = !INTRADAY.has(interval)

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
      <div className="flex items-center gap-1 px-2 py-1 border-b border-border shrink-0 flex-wrap">
        {INTERVALS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setInterval(key)}
            className={`px-2 py-0.5 text-xs rounded transition-colors ${
              interval === key
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent'
            }`}
          >
            {label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-1">
          {[
            { key: 'sr',      label: 'S/R',   active: showSR,      set: setShowSR },
            { key: 'trend',   label: '추세선', active: showTrend,   set: setShowTrend },
            { key: 'anomaly', label: '이상감지', active: showAnomaly, set: setShowAnomaly },
          ].map(({ key, label, active, set }) => (
            <button
              key={key}
              onClick={() => set((v) => !v)}
              className={cn(
                'px-2 py-0.5 text-[11px] rounded border transition-colors',
                active
                  ? 'bg-primary/20 border-primary/50 text-primary'
                  : 'border-border text-muted-foreground hover:text-foreground'
              )}
            >
              {label}
            </button>
          ))}
        </div>
        {loadingIntraday && (
          <span className="text-xs text-muted-foreground">분봉 불러오는 중 · 일봉 임시 표시</span>
        )}
      </div>
      {showPeriodBar && (
        <div className="flex items-center gap-1 px-2 py-0.5 border-b border-border shrink-0 bg-muted/30">
          <span className="text-[11px] text-muted-foreground mr-1">기간</span>
          {PERIODS.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setPeriod(key)}
              className={`px-2 py-0.5 text-[11px] rounded transition-colors ${
                period === key
                  ? 'bg-accent text-foreground font-medium'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent/60'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      )}
      <PatternBadges patterns={patterns} />
      <div className="flex flex-col flex-1 min-h-0 gap-0.5 p-1">
        <div className="flex-[3] min-h-0">
          <CandleChart candles={candles} onChartReady={setChart} />
          {!INTRADAY.has(interval) && (
            <PredictionOverlay
              chart={chart}
              prediction={prediction}
              lastCandleTime={lastCandleTime}
            />
          )}
          {showSR && <SupportResistanceOverlay chart={chart} candles={candles} data={srData} />}
          {showTrend && <TrendlineOverlay chart={chart} data={trendlineData} />}
        </div>
        <div className="flex-1 min-h-0">
          <RSIChart data={rsiData} />
        </div>
        <div className="flex-1 min-h-0">
          <MACDChart data={macdData} />
        </div>
        {showAnomaly && (
          <div className="flex-1 min-h-0">
            <AnomalyChart data={anomalyData} />
          </div>
        )}
      </div>
    </div>
  )
}
