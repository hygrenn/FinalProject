import { act, renderHook } from '@testing-library/react'
import { useStockStore } from '@/store/stockStore'
import { useUIStore } from '@/store/uiStore'
import { MOCK_STOCKS, MOCK_WATCHLIST } from '@/lib/mockData'

beforeEach(() => {
  // Reset Zustand singletons to initial state before each test
  useStockStore.setState({
    selectedStock: MOCK_STOCKS[0],
    watchlist: [...MOCK_WATCHLIST],
    stockList: MOCK_STOCKS,
  })
  useUIStore.setState({
    darkMode: true,
    activeTab: 'chart',
    sidebarOpen: true,
  })
})

describe('stockStore', () => {
  it('initial selectedStock is first mock stock', () => {
    const { result } = renderHook(() => useStockStore())
    expect(result.current.selectedStock?.code).toBe('005930')
  })

  it('addToWatchlist adds unique code', () => {
    const { result } = renderHook(() => useStockStore())
    const initialLen = result.current.watchlist.length
    act(() => result.current.addToWatchlist('999999'))
    expect(result.current.watchlist).toContain('999999')
    expect(result.current.watchlist.length).toBe(initialLen + 1)
  })

  it('addToWatchlist does not duplicate', () => {
    const { result } = renderHook(() => useStockStore())
    const existingCode = result.current.watchlist[0]
    const before = result.current.watchlist.length
    act(() => result.current.addToWatchlist(existingCode))
    expect(result.current.watchlist.length).toBe(before)
  })

  it('removeFromWatchlist removes code', () => {
    const { result } = renderHook(() => useStockStore())
    const code = result.current.watchlist[0]
    act(() => result.current.removeFromWatchlist(code))
    expect(result.current.watchlist).not.toContain(code)
  })
})

describe('uiStore', () => {
  it('default darkMode is true', () => {
    const { result } = renderHook(() => useUIStore())
    expect(result.current.darkMode).toBe(true)
  })

  it('toggleDarkMode flips darkMode', () => {
    const { result } = renderHook(() => useUIStore())
    act(() => result.current.toggleDarkMode())
    expect(result.current.darkMode).toBe(false)
    act(() => result.current.toggleDarkMode())
    expect(result.current.darkMode).toBe(true)
  })

  it('setActiveTab updates activeTab', () => {
    const { result } = renderHook(() => useUIStore())
    act(() => result.current.setActiveTab('ai'))
    expect(result.current.activeTab).toBe('ai')
  })
})
