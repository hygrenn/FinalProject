// frontend/src/components/WatchlistPanel/WatchlistPanel.tsx
import { useStockStore } from '@/store/stockStore'
import { cn } from '@/lib/utils'

export function WatchlistPanel() {
  const { stockList, watchlist, selectedStock, setSelectedStock } = useStockStore()
  const stocks = stockList.filter((s) => watchlist.includes(s.code))

  return (
    <div className="h-8 flex items-center gap-4 px-4 bg-card border-t border-border overflow-x-auto shrink-0">
      {stocks.map((stock) => (
        <button
          key={stock.code}
          onClick={() => setSelectedStock(stock)}
          className={cn(
            'flex items-center gap-2 text-xs whitespace-nowrap hover:text-foreground',
            selectedStock?.code === stock.code ? 'text-foreground' : 'text-muted-foreground'
          )}
        >
          <span className="font-medium">{stock.name}</span>
          {stock.price && (
            <span>{stock.price.toLocaleString('ko-KR')}</span>
          )}
          {stock.change_pct !== undefined && (
            <span className={stock.change_pct >= 0 ? 'text-green-500' : 'text-red-500'}>
              {stock.change_pct >= 0 ? '▲' : '▼'}{Math.abs(stock.change_pct).toFixed(1)}%
            </span>
          )}
        </button>
      ))}
    </div>
  )
}
