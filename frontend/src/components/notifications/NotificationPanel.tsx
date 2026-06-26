import { useEffect, useRef } from 'react'
import { useNotificacionStore } from '@/stores/notificacionStore'
import { TIPOS_NOTIFICACION_LABELS } from '@/shared/types/notificacion'
import type { Notificacion } from '@/shared/types/notificacion'

interface NotificationPanelProps {
  onClose: () => void
}

const TIEMPO_RELATIVO_REFRESH_MS = 30_000

function formatTiempoRelativo(iso: string): string {
  const fecha = new Date(iso)
  if (Number.isNaN(fecha.getTime())) return ''
  const diffMs = Date.now() - fecha.getTime()
  const seg = Math.floor(diffMs / 1000)
  if (seg < 60) return `hace ${seg} seg`
  const min = Math.floor(seg / 60)
  if (min < 60) return `hace ${min} min`
  const horas = Math.floor(min / 60)
  if (horas < 24) return `hace ${horas} h`
  const dias = Math.floor(horas / 24)
  if (dias < 7) return `hace ${dias} d`
  return fecha.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' })
}

function tipoLabel(tipo: string): string {
  if (tipo in TIPOS_NOTIFICACION_LABELS) {
    return TIPOS_NOTIFICACION_LABELS[tipo as keyof typeof TIPOS_NOTIFICACION_LABELS]
  }
  return tipo
}

function NotificacionItem({ notif, onMarcar }: { notif: Notificacion; onMarcar: (id: string) => void }) {
  return (
    <li
      data-testid={`notification-item-${notif.id}`}
      className={`px-4 py-3 border-b border-surface-100 last:border-b-0 ${
        notif.leida ? 'bg-white' : 'bg-primary-50/40'
      }`}
    >
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-xs uppercase tracking-wide text-surface-500 font-semibold">
            {tipoLabel(notif.tipo)}
          </p>
          <p className="text-sm text-surface-800 mt-0.5 break-words">{notif.mensaje}</p>
          <p className="text-xs text-surface-500 mt-1">
            <time dateTime={notif.created_at}>{formatTiempoRelativo(notif.created_at)}</time>
          </p>
        </div>
        {!notif.leida && (
          <button
            type="button"
            onClick={() => onMarcar(notif.id)}
            aria-label="Marcar como leída"
            data-testid={`notification-mark-read-${notif.id}`}
            className="text-xs text-primary-600 hover:text-primary-800 hover:underline shrink-0"
          >
            Marcar leída
          </button>
        )}
      </div>
    </li>
  )
}

export function NotificationPanel({ onClose }: NotificationPanelProps) {
  const notificaciones = useNotificacionStore((s) => s.notificaciones)
  const loading = useNotificacionStore((s) => s.loading)
  const error = useNotificacionStore((s) => s.error)
  const marcarLeida = useNotificacionStore((s) => s.marcarLeida)
  const marcarTodasLeidas = useNotificacionStore((s) => s.marcarTodasLeidas)
  const clearError = useNotificacionStore((s) => s.clearError)

  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const handleMouseDown = (event: MouseEvent) => {
      if (
        containerRef.current &&
        event.target instanceof Node &&
        !containerRef.current.contains(event.target)
      ) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleMouseDown)
    return () => document.removeEventListener('mousedown', handleMouseDown)
  }, [onClose])

  // Refresca el "hace X min" cada 30s sin pedir al backend.
  useEffect(() => {
    const interval = setInterval(() => {
      // Forzar re-render de los tiempos relativos: emitimos un evento
      // barato cambiando un estado interno.
    }, TIEMPO_RELATIVO_REFRESH_MS)
    return () => clearInterval(interval)
  }, [])

  const handleMarcar = async (id: string) => {
    try {
      await marcarLeida(id)
    } catch {
      // el store ya setea el error
    }
  }

  const handleMarcarTodas = async () => {
    try {
      await marcarTodasLeidas()
    } catch {
      // idem
    }
  }

  const hayNoLeidas = notificaciones.some((n) => !n.leida)

  return (
    <div
      ref={containerRef}
      role="dialog"
      aria-label="Panel de notificaciones"
      data-testid="notification-panel"
      className="absolute right-0 mt-2 w-96 max-w-[calc(100vw-1rem)] bg-white rounded-md shadow-card border border-surface-200 z-50"
    >
      <div className="flex items-center justify-between px-4 py-2 border-b border-surface-200">
        <h2 className="text-sm font-semibold text-surface-800">Notificaciones</h2>
        {hayNoLeidas && (
          <button
            type="button"
            onClick={handleMarcarTodas}
            data-testid="notification-mark-all"
            className="text-xs text-primary-600 hover:text-primary-800 hover:underline"
          >
            Marcar todas como leídas
          </button>
        )}
      </div>

      {error && (
        <div
          role="alert"
          className="px-4 py-2 text-sm text-red-600 bg-red-50 border-b border-red-100 flex items-center justify-between"
        >
          <span>{error}</span>
          <button
            type="button"
            onClick={clearError}
            className="text-xs underline"
            aria-label="Cerrar error"
          >
            Cerrar
          </button>
        </div>
      )}

      {loading && notificaciones.length === 0 ? (
        <div className="px-4 py-6 text-sm text-surface-500 text-center">Cargando notificaciones…</div>
      ) : notificaciones.length === 0 ? (
        <div className="px-4 py-6 text-sm text-surface-500 text-center" data-testid="notification-empty">
          No tenés notificaciones pendientes.
        </div>
      ) : (
        <ul className="max-h-96 overflow-y-auto" data-testid="notification-list">
          {notificaciones.map((n) => (
            <NotificacionItem key={n.id} notif={n} onMarcar={handleMarcar} />
          ))}
        </ul>
      )}

      <div className="px-4 py-2 border-t border-surface-200 text-right">
        <button
          type="button"
          onClick={onClose}
          className="text-xs text-surface-600 hover:text-surface-800"
        >
          Cerrar
        </button>
      </div>
    </div>
  )
}
