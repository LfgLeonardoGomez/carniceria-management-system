import { create } from 'zustand'
import type {
  AuditoriaFilters,
  AuditoriaRegistro,
} from '@/shared/types/auditoria'
import {
  fetchAuditoria,
  exportarCSV,
  exportarJSON,
} from '@/features/auditoria/api'

interface AuditoriaState {
  registros: AuditoriaRegistro[]
  total: number
  loading: boolean
  error: string | null
  filters: AuditoriaFilters
  setFilters: (filters: Partial<AuditoriaFilters>) => void
  fetchAuditoria: (override?: Partial<AuditoriaFilters>) => Promise<void>
  exportarCSV: () => Blob
  exportarJSON: () => Blob
  clearError: () => void
}

export const useAuditoriaStore = create<AuditoriaState>((set, get) => ({
  registros: [],
  total: 0,
  loading: false,
  error: null,
  filters: { skip: 0, limit: 50 },

  setFilters: (filters) => {
    const merged = { ...get().filters, ...filters, skip: 0 }
    set({ filters: merged })
    get().fetchAuditoria()
  },

  fetchAuditoria: async (override) => {
    const filters: AuditoriaFilters = {
      ...get().filters,
      ...(override ?? {}),
      skip: override?.skip ?? get().filters.skip ?? 0,
    }
    set({ loading: true, error: null, filters })
    try {
      const response = await fetchAuditoria(filters)
      set({
        registros: response.items,
        total: response.total,
        loading: false,
      })
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Error al cargar auditoría'
      set({ loading: false, error: message })
    }
  },

  exportarCSV: () => exportarCSV(get().registros),
  exportarJSON: () => exportarJSON(get().registros),

  clearError: () => set({ error: null }),
}))
