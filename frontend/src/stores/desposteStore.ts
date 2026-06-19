import { create } from 'zustand'
import type {
  Desposte,
  DesposteCreate,
  CorteDesposteCreate,
  DesposteFilters,
  TipoCorte,
} from '@/shared/types/desposte'
import {
  fetchDespostes,
  fetchDesposte,
  createDesposte,
  addCorte,
  finalizarDesposte,
} from '@/features/despostes/api'

interface DesposteState {
  despostes: Desposte[]
  totalDespostes: number
  selectedDesposte: Desposte | null
  loading: boolean
  error: string | null
  filters: DesposteFilters
  wizardData: {
    compraId: string
    fecha: string
    operadorId: string
    cortes: Map<TipoCorte, { kilos: string; productoId: string | null }>
  }
  setFilters: (filters: Partial<DesposteFilters>) => void
  fetchDespostes: () => Promise<void>
  fetchDesposte: (id: string) => Promise<void>
  createDesposte: (dto: DesposteCreate) => Promise<Desposte>
  addCorte: (desposteId: string, dto: CorteDesposteCreate) => Promise<void>
  finalizarDesposte: (id: string) => Promise<void>
  setWizardData: (data: Partial<DesposteState['wizardData']>) => void
  setCorteWizard: (tipo: TipoCorte, kilos: string, productoId: string | null) => void
  clearError: () => void
  clearSelected: () => void
  clearWizard: () => void
}

export const useDesposteStore = create<DesposteState>((set, get) => ({
  despostes: [],
  totalDespostes: 0,
  selectedDesposte: null,
  loading: false,
  error: null,
  filters: {
    skip: 0,
    limit: 20,
  },
  wizardData: {
    compraId: '',
    fecha: new Date().toISOString().split('T')[0],
    operadorId: '',
    cortes: new Map(),
  },

  setFilters: (filters: Partial<DesposteFilters>) => {
    set({ filters: { ...get().filters, ...filters, skip: 0 } })
    get().fetchDespostes()
  },

  fetchDespostes: async () => {
    set({ loading: true, error: null })
    try {
      const response = await fetchDespostes(get().filters)
      set({
        despostes: response.items,
        totalDespostes: response.total,
        loading: false,
      })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar despostes'
      set({ error: msg, loading: false })
    }
  },

  fetchDesposte: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const desposte = await fetchDesposte(id)
      set({ selectedDesposte: desposte, loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar desposte'
      set({ error: msg, loading: false })
    }
  },

  createDesposte: async (dto: DesposteCreate) => {
    set({ loading: true, error: null })
    try {
      const desposte = await createDesposte(dto)
      set({
        despostes: [desposte, ...get().despostes],
        totalDespostes: get().totalDespostes + 1,
        loading: false,
      })
      return desposte
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al crear desposte'
      set({ error: msg, loading: false })
      throw err
    }
  },

  addCorte: async (desposteId: string, dto: CorteDesposteCreate) => {
    set({ loading: true, error: null })
    try {
      await addCorte(desposteId, dto)
      set({ loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al agregar corte'
      set({ error: msg, loading: false })
      throw err
    }
  },

  finalizarDesposte: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const desposte = await finalizarDesposte(id)
      set({
        despostes: get().despostes.map((d) => (d.id === id ? desposte : d)),
        selectedDesposte: desposte,
        loading: false,
      })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al finalizar desposte'
      set({ error: msg, loading: false })
      throw err
    }
  },

  setWizardData: (data: Partial<DesposteState['wizardData']>) => {
    set({ wizardData: { ...get().wizardData, ...data } })
  },

  setCorteWizard: (tipo: TipoCorte, kilos: string, productoId: string | null) => {
    const next = new Map(get().wizardData.cortes)
    next.set(tipo, { kilos, productoId })
    set({ wizardData: { ...get().wizardData, cortes: next } })
  },

  clearError: () => set({ error: null }),
  clearSelected: () => set({ selectedDesposte: null }),
  clearWizard: () =>
    set({
      wizardData: {
        compraId: '',
        fecha: new Date().toISOString().split('T')[0],
        operadorId: '',
        cortes: new Map(),
      },
    }),
}))
