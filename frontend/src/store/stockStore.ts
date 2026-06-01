// frontend/src/store/stockStore.ts
import { create } from 'zustand'
import type { Stock } from '@/types'
import { MOCK_STOCKS, MOCK_WATCHLIST } from '@/lib/mockData'

interface StockState {
  selectedStock: Stock | null
  watchlist: string[]
  stockList: Stock[]
  setSelectedStock: (stock: Stock) => void
  addToWatchlist: (code: string) => void
  removeFromWatchlist: (code: string) => void
}

export const useStockStore = create<StockState>((set) => ({
  selectedStock: MOCK_STOCKS[0],
  watchlist: MOCK_WATCHLIST,
  stockList: MOCK_STOCKS,

  setSelectedStock: (stock) => set({ selectedStock: stock }),

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
}))
