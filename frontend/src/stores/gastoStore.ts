import { create } from 'zustand'
import type { Gasto, GastoCreate, GastoUpdate, CategoriaGasto, GastoFilters } from '@/shared/types/gasto'
import { fetchGastos, fetchGasto, createGasto, updateGasto, deleteGasto } from '@/features/gastos/api'

interface GastoState {
  gastos: Gasto[]
  totalGastos: number
  selectedGasto: Gasto | null
  loading: boolean
  error: string | null
  filters: GastoFilters
  setFilters: (filters: GastoFilters) => void
  setCategoria: (categoria: CategoriaGasto | undefined) => void
  setFechaRango: (desde: string, hasta: string) => void
  fetchGastos: () => Promise<void>
  fetchGasto: (id: string) => Promise<void>
  createGasto: (dto: GastoCreate) => Promise<Gasto>
  updateGasto: (id: string, dto: GastoUpdate) => Promise<Gasto>
  deleteGasto: (id: string) => Promise<void>
  clearError: () => void
  clearSelected: () => void
}

export const useGastoStore = create<GastoState>((set, get) => ({
  gastos: [],
  totalGastos: 0,
  selectedGasto: null,
  loading: false,
  error: null,
  filters: { skip: 0, limit: 20 },

  setFilters: (filters: GastoFilters) => {
    set({ filters: { ...get().filters, ...filters, skip: 0 } })
    get().fetchGastos()
  },

  setCategoria: (categoria: CategoriaGasto | undefined) => {
    set({ filters: { ...get().filters, categoria, skip: 0 } })
    get().fetchGastos()
  },

  setFechaRango: (desde: string, hasta: string) => {
    set({
      filters: {
        ...get().filters,
        fecha_desde: desde || undefined,
        fecha_hasta: hasta || undefined,
        skip: 0,
      },
    })
    get().fetchGastos()
  },

  fetchGastos: async () => {
    set({ loading: true, error: null })
    try {
      const { filters } = get()
      const response = await fetchGastos(filters)
      set({ gastos: response.items, totalGastos: response.total, loading: false })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al cargar gastos'
      set({ loading: false, error: message })
    }
  },

  fetchGasto: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const gasto = await fetchGasto(id)
      set({ selectedGasto: gasto, loading: false })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al cargar gasto'
      set({ loading: false, error: message })
    }
  },

  createGasto: async (dto: GastoCreate) => {
    set({ loading: true, error: null })
    try {
      const gasto = await createGasto(dto)
      await get().fetchGastos()
      set({ loading: false })
      return gasto
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al crear gasto'
      set({ loading: false, error: message })
      throw err
    }
  },

  updateGasto: async (id: string, dto: GastoUpdate) => {
    set({ loading: true, error: null })
    try {
      const gasto = await updateGasto(id, dto)
      await get().fetchGastos()
      set({ loading: false })
      return gasto
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al actualizar gasto'
      set({ loading: false, error: message })
      throw err
    }
  },

  deleteGasto: async (id: string) => {
    set({ loading: true, error: null })
    try {
      await deleteGasto(id)
      await get().fetchGastos()
      set({ loading: false })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al eliminar gasto'
      set({ loading: false, error: message })
      throw err
    }
  },

  clearError: () => set({ error: null }),
  clearSelected: () => set({ selectedGasto: null }),
}))
