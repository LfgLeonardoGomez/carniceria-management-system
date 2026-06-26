import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { MenuIcon, UserCircleIcon, LogoutIcon } from '@/components/layout/icons'
import { NotificationBadge } from '@/components/notifications/NotificationBadge'
import { NotificationPanel } from '@/components/notifications/NotificationPanel'

interface HeaderProps {
  onToggleSidebar: () => void
}

function getInitials(nombre?: string, apellido?: string): string {
  const n = (nombre ?? '').trim().charAt(0)
  const a = (apellido ?? '').trim().charAt(0)
  return `${n}${a}`.toUpperCase() || '?'
}

export function Header({ onToggleSidebar }: HeaderProps) {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  // TODO: conectar empresa context — leer `empresa.nombre_comercial` cuando exista
  const empresaNombre = 'BASILE'

  const [open, setOpen] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const userRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open && !notifOpen) return
    const handleMouseDown = (event: MouseEvent) => {
      const target = event.target
      if (!(target instanceof Node)) return
      const insideUser = userRef.current?.contains(target) ?? false
      const insideContainer = containerRef.current?.contains(target) ?? false
      if (!insideUser) setOpen(false)
      if (!insideContainer) setNotifOpen(false)
    }
    document.addEventListener('mousedown', handleMouseDown)
    return () => document.removeEventListener('mousedown', handleMouseDown)
  }, [open, notifOpen])

  const handleLogout = () => {
    logout()
    localStorage.removeItem('access_token')
    setOpen(false)
    navigate('/login')
  }

  const handleProfile = () => {
    setOpen(false)
    navigate('/perfil')
  }

  const handleToggleNotifications = () => {
    setNotifOpen((v) => !v)
    setOpen(false)
  }

  const fullName = user ? `${user.nombre} ${user.apellido}`.trim() : ''

  return (
    <header
      data-testid="header"
      className="h-14 bg-white border-b border-surface-200 flex items-center px-4 gap-4"
    >
      <button
        type="button"
        onClick={onToggleSidebar}
        aria-label="Toggle menú lateral"
        className="p-2 rounded-md text-surface-600 hover:bg-surface-100 hover:text-surface-900 transition-colors"
      >
        <MenuIcon className="w-5 h-5" />
      </button>

      <div className="flex-1 flex items-center justify-center">
        <span className="text-lg font-bold text-primary-600 tracking-wide" data-testid="brand">
          {empresaNombre}
        </span>
      </div>

      <div className="relative" ref={containerRef}>
        <NotificationBadge onToggle={handleToggleNotifications} open={notifOpen} />
        {notifOpen && <NotificationPanel onClose={() => setNotifOpen(false)} />}
      </div>

      <div className="relative" ref={userRef}>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-haspopup="menu"
          aria-expanded={open}
          className="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm font-medium text-surface-700 hover:bg-surface-100 transition-colors"
        >
          <span
            aria-hidden="true"
            className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-semibold"
          >
            {getInitials(user?.nombre, user?.apellido)}
          </span>
          <span className="hidden sm:inline">{fullName}</span>
          <UserCircleIcon className="w-5 h-5 text-surface-500" />
        </button>

        {open && (
          <div
            role="menu"
            data-testid="user-dropdown"
            className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-card border border-surface-200 py-1 z-50"
          >
            <button
              type="button"
              role="menuitem"
              onClick={handleProfile}
              className="w-full text-left px-4 py-2 text-sm text-surface-700 hover:bg-surface-100"
            >
              Mi perfil
            </button>
            <button
              type="button"
              role="menuitem"
              onClick={handleLogout}
              className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
            >
              <LogoutIcon className="w-4 h-4" />
              Cerrar sesión
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
