// frontend/src/store/stockStore.ts
import { create } from 'zustand'
import type { Stock, RealtimePrice } from '@/types'
import { MOCK_STOCKS, MOCK_WATCHLIST } from '@/lib/mockData'

interface StockState {
  selectedStock: Stock | null
  watchlist: string[]
  stockList: Stock[]
  realtimePrice: RealtimePrice | null
  setSelectedStock: (stock: Stock) => void
  addToWatchlist: (code: string) => void
  removeFromWatchlist: (code: string) => void
  updateRealtimePrice: (data: RealtimePrice) => void
}

export const useStockStore = create<StockState>((set) => ({
  selectedStock: MOCK_STOCKS[0],
  watchlist: MOCK_WATCHLIST,
  stockList: MOCK_STOCKS,
  realtimePrice: null,

  setSelectedStock: (stock) => set({ selectedStock: stock, realtimePrice: null }),

  addToWatchlist: (code) =>
    set((state) => ({
      watchlist: state.watchlist.includes(code)
        ? state.watchlist
        : [...state.watchlist, code],
    })),

  removeFromWatchlist: (code) =>
    set((state) => ({
      watchlist: state.watchlist.filter((c) => c !== code),
    })),

  updateRealtimePrice: (data) => set({ realtimePrice: data }),
}))
