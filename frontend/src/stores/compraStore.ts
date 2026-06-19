import { create } from 'zustand'
import type { Compra, CompraCreate, CompraUpdate, CompraFilters } from '@/shared/types/compra'
import {
  fetchCompras,
  fetchCompra,
  createCompra,
  updateCompra,
  deleteCompra,
} from '@/features/compras/api'

interface CompraState {
  compras: Compra[]
  totalCompras: number
  selectedCompra: Compra | null
  loading: boolean
  error: string | null
  filters: CompraFilters
  setFilters: (filters: Partial<CompraFilters>) => void
  fetchCompras: () => Promise<void>
  fetchCompra: (id: string) => Promise<void>
  createCompra: (dto: CompraCreate) => Promise<Compra>
  updateCompra: (id: string, dto: CompraUpdate) => Promise<Compra>
  deleteCompra: (id: string) => Promise<void>
  clearError: () => void
  clearSelected: () => void
}

export const useCompraStore = create<CompraState>((set, get) => ({
  compras: [],
  totalCompras: 0,
  selectedCompra: null,
  loading: false,
  error: null,
  filters: {
    skip: 0,
    limit: 20,
  },

  setFilters: (filters: Partial<CompraFilters>) => {
    set({ filters: { ...get().filters, ...filters, skip: 0 } })
    get().fetchCompras()
  },

  fetchCompras: async () => {
    set({ loading: true, error: null })
    try {
      const response = await fetchCompras(get().filters)
      set({
        compras: response.items,
        totalCompras: response.total,
        loading: false,
      })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar compras'
      set({ error: msg, loading: false })
    }
  },

  fetchCompra: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const compra = await fetchCompra(id)
      set({ selectedCompra: compra, loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar compra'
      set({ error: msg, loading: false })
    }
  },

  createCompra: async (dto: CompraCreate) => {
    set({ loading: true, error: null })
    try {
      const compra = await createCompra(dto)
      set({
        compras: [compra, ...get().compras],
        totalCompras: get().totalCompras + 1,
        loading: false,
      })
      return compra
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al crear compra'
      set({ error: msg, loading: false })
      throw err
    }
  },

  updateCompra: async (id: string, dto: CompraUpdate) => {
    set({ loading: true, error: null })
    try {
      const compra = await updateCompra(id, dto)
      set({
        compras: get().compras.map((c) => (c.id === id ? compra : c)),
        selectedCompra: get().selectedCompra?.id === id ? compra : get().selectedCompra,
        loading: false,
      })
      return compra
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al actualizar compra'
      set({ error: msg, loading: false })
      throw err
    }
  },

  deleteCompra: async (id: string) => {
    set({ loading: true, error: null })
    try {
      await deleteCompra(id)
      set({
        compras: get().compras.map((c) => (c.id === id ? { ...c, estado: 'anulada' } as Compra : c)),
        selectedCompra: get().selectedCompra?.id === id ? { ...get().selectedCompra, estado: 'anulada' } as Compra : get().selectedCompra,
        loading: false,
      })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al anular compra'
      set({ error: msg, loading: false })
      throw err
    }
  },

  clearError: () => set({ error: null }),
  clearSelected: () => set({ selectedCompra: null }),
}))
