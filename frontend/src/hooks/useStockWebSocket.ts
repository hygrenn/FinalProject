import { useEffect, useState } from 'react'
import { MockWebSocket } from '@/lib/mockWebSocket'
import { useStockStore } from '@/store/stockStore'

const WS_BASE = import.meta.env.VITE_WS_BASE ?? null

export function useStockWebSocket(stockCode: string): { isConnected: boolean } {
  const [isConnected, setIsConnected] = useState(false)
  const updateRealtimePrice = useStockStore((s) => s.updateRealtimePrice)

  useEffect(() => {
    const url = WS_BASE
      ? `${WS_BASE}/ws/stocks/${stockCode}`
      : `mock://stocks/${stockCode}`

    const ws = WS_BASE
      ? (new WebSocket(url) as unknown as MockWebSocket)
      : new MockWebSocket(url)

    ws.onopen = () => setIsConnected(true)
    ws.onclose = () => setIsConnected(false)
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        updateRealtimePrice({ code: stockCode, price: data.price, change_pct: data.change_pct })
      } catch {}
    }

    return () => {
      ws.close()
      setIsConnected(false)
    }
  }, [stockCode, updateRealtimePrice])

  return { isConnected }
}
