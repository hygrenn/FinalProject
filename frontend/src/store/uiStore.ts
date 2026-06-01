// frontend/src/store/uiStore.ts
import { create } from 'zustand'
import type { TabId } from '@/types'

interface UIState {
  darkMode: boolean
  activeTab: TabId
  sidebarOpen: boolean
  toggleDarkMode: () => void
  setActiveTab: (tab: TabId) => void
  toggleSidebar: () => void
}

export const useUIStore = create<UIState>((set) => ({
  darkMode: true,
  activeTab: 'chart',
  sidebarOpen: true,

  toggleDarkMode: () =>
    set((state) => {
      const next = !state.darkMode
      document.documentElement.classList.toggle('dark', next)
      return { darkMode: next }
    }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  toggleSidebar: () =>
    set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}))
