// frontend/src/components/MainPanel/ChartTab/ChartTab.tsx
import { useEffect, useRef } from 'react'
import { createChart, ColorType } from 'lightweight-charts'
import { useStockStore } from '@/store/stockStore'
import { MOCK_CANDLES } from '@/lib/mockData'

export function ChartTab() {
  const chartRef = useRef<HTMLDivElement>(null)
  const { selectedStock } = useStockStore()

  useEffect(() => {
    if (!chartRef.current) return

    const chart = createChart(chartRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { color: '#1f2937' },
        horzLines: { color: '#1f2937' },
      },
      width: chartRef.current.clientWidth,
      height: chartRef.current.clientHeight,
    })

    const series = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })

    series.setData(MOCK_CANDLES)
    chart.timeScale().fitContent()

    const handleResize = () => {
      if (chartRef.current) {
        chart.applyOptions({ width: chartRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [selectedStock])

  return (
    <div className="flex flex-col h-full p-2 gap-2">
      <div className="flex items-center gap-3 px-2">
        <span className="font-semibold">{selectedStock?.name}</span>
        <span className="text-muted-foreground text-sm">{selectedStock?.code}</span>
        {selectedStock?.price && (
          <span className="font-bold">{selectedStock.price.toLocaleString()}원</span>
        )}
        {selectedStock?.change_pct !== undefined && (
          <span className={selectedStock.change_pct >= 0 ? 'text-green-500' : 'text-red-500'}>
            {selectedStock.change_pct >= 0 ? '+' : ''}{selectedStock.change_pct.toFixed(1)}%
          </span>
        )}
      </div>
      <div ref={chartRef} className="flex-1 min-h-0" />
    </div>
  )
}
