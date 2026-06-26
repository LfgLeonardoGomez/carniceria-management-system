import { BellIcon } from '@/components/layout/icons'
import { useNotificacionStore } from '@/stores/notificacionStore'

interface NotificationBadgeProps {
  onToggle: () => void
  open: boolean
}

function formatCount(count: number): string {
  if (count > 99) return '99+'
  return String(count)
}

export function NotificationBadge({ onToggle, open }: NotificationBadgeProps) {
  const unreadCount = useNotificacionStore((s) => s.unreadCount)

  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label="Notificaciones"
      aria-haspopup="dialog"
      aria-expanded={open}
      data-testid="notification-badge-button"
      className={`relative p-2 rounded-md transition-colors ${
        open
          ? 'bg-primary-50 text-primary-700'
          : 'text-surface-600 hover:bg-surface-100 hover:text-surface-900'
      }`}
    >
      <BellIcon className="w-5 h-5" aria-hidden="true" />
      {unreadCount > 0 && (
        <span
          data-testid="notification-badge-count"
          aria-label={`${unreadCount} notificaciones sin leer`}
          className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 inline-flex items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-semibold leading-none"
        >
          {formatCount(unreadCount)}
        </span>
      )}
    </button>
  )
}
