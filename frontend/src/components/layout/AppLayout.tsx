import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { useNotificacionStore } from '@/stores/notificacionStore'

const COLLAPSED_KEY = 'basile.sidebar.collapsed'
const NOTIF_POLLING_MS = 60_000

function readInitialCollapsed(): boolean {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === 'true'
  } catch {
    return false
  }
}

interface AppLayoutProps {
  children: ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const [collapsed, setCollapsed] = useState<boolean>(() => readInitialCollapsed())
  const fetchNotificaciones = useNotificacionStore((s) => s.fetchNotificaciones)

  useEffect(() => {
    try {
      localStorage.setItem(COLLAPSED_KEY, String(collapsed))
    } catch {
      /* localStorage unavailable */
    }
  }, [collapsed])

  // Carga inicial + polling periódico del contador de no leídas.
  useEffect(() => {
    fetchNotificaciones()
    const interval = setInterval(() => {
      fetchNotificaciones()
    }, NOTIF_POLLING_MS)
    return () => clearInterval(interval)
  }, [fetchNotificaciones])

  const toggle = useCallback(() => setCollapsed((v) => !v), [])

  return (
    <div className="flex h-screen bg-surface-50">
      <Sidebar collapsed={collapsed} onToggle={toggle} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onToggleSidebar={toggle} />
        <main className="flex-1 overflow-auto p-6" data-testid="app-main">
          {children}
        </main>
      </div>
    </div>
  )
}
