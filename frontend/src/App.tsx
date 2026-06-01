// frontend/src/App.tsx
import { useState, useEffect } from 'react'
import { LandingPage } from '@/pages/LandingPage'
import { MainLayout } from '@/components/Layout/MainLayout'
import { useUIStore } from '@/store/uiStore'
import { useAuthStore } from '@/store/authStore'

export default function App() {
  const [entered, setEntered] = useState(false)
  const { darkMode } = useUIStore()
  const { user } = useAuthStore()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])

  if (!entered && !user) {
    return <LandingPage onEnter={() => setEntered(true)} />
  }

  return <MainLayout />
}
