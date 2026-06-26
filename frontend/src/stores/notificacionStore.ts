import { create } from 'zustand'
import type {
  Notificacion,
  NotificacionFilters,
} from '@/shared/types/notificacion'
import {
  fetchNotificaciones,
  marcarLeida as apiMarcarLeida,
} from '@/features/notifications/api'

interface NotificacionState {
  notificaciones: Notificacion[]
  total: number
  unreadCount: number
  loading: boolean
  error: string | null
  filters: NotificacionFilters
  fetchNotificaciones: (filters?: Partial<NotificacionFilters>) => Promise<void>
  refrescar: () => Promise<void>
  marcarLeida: (id: string) => Promise<void>
  marcarTodasLeidas: () => Promise<void>
  clearError: () => void
}

export const useNotificacionStore = create<NotificacionState>((set, get) => ({
  notificaciones: [],
  total: 0,
  unreadCount: 0,
  loading: false,
  error: null,
  filters: { skip: 0, limit: 50, leida: false },

  fetchNotificaciones: async (override) => {
    const filters: NotificacionFilters = {
      ...get().filters,
      ...(override ?? {}),
      skip: override?.skip ?? 0,
    }
    set({ loading: true, error: null, filters })
    try {
      const response = await fetchNotificaciones(filters)
      const unread = response.items.filter((n) => !n.leida).length
      set({
        notificaciones: response.items,
        total: response.total,
        unreadCount: unread,
        loading: false,
      })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al cargar notificaciones'
      set({ loading: false, error: message })
    }
  },

  refrescar: async () => {
    await get().fetchNotificaciones()
  },

  marcarLeida: async (id) => {
    set({ error: null })
    try {
      await apiMarcarLeida(id)
      set((state) => {
        const updated = state.notificaciones.map((n) =>
          n.id === id ? { ...n, leida: true, fecha_lectura: new Date().toISOString() } : n,
        )
        const unread = updated.filter((n) => !n.leida).length
        return { notificaciones: updated, unreadCount: unread }
      })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al marcar notificación como leída'
      set({ error: message })
      throw err
    }
  },

  marcarTodasLeidas: async () => {
    const pendientes = get().notificaciones.filter((n) => !n.leida)
    set({ error: null })
    const errores: unknown[] = []
    for (const n of pendientes) {
      try {
        await apiMarcarLeida(n.id)
      } catch (err) {
        errores.push(err)
      }
    }
    set((state) => {
      const updated = state.notificaciones.map((notif) =>
        notif.leida
          ? notif
          : { ...notif, leida: true, fecha_lectura: new Date().toISOString() },
      )
      return { notificaciones: updated, unreadCount: 0 }
    })
    if (errores.length > 0) {
      set({ error: 'Algunas notificaciones no pudieron marcarse como leídas' })
    }
  },

  clearError: () => set({ error: null }),
}))
