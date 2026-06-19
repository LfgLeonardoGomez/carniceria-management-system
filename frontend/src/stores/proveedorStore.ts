import { create } from 'zustand'
import type { Proveedor, ProveedorCreate, ProveedorUpdate } from '@/shared/types/proveedor'
import {
  fetchProveedores,
  fetchProveedor,
  createProveedor,
  updateProveedor,
  deleteProveedor,
  fetchProveedorHistorial,
} from '@/features/proveedores/api'

interface ProveedorState {
  proveedores: Proveedor[]
  totalProveedores: number
  selectedProveedor: Proveedor | null
  historial: { items: unknown[]; total: number }
  loading: boolean
  error: string | null
  searchQuery: string
  skip: number
  limit: number
  incluirInactivos: boolean
  setSearchQuery: (q: string) => void
  setSkip: (skip: number) => void
  setLimit: (limit: number) => void
  setIncluirInactivos: (v: boolean) => void
  fetchProveedores: () => Promise<void>
  fetchProveedor: (id: string) => Promise<void>
  fetchHistorial: (id: string) => Promise<void>
  createProveedor: (dto: ProveedorCreate) => Promise<Proveedor>
  updateProveedor: (id: string, dto: ProveedorUpdate) => Promise<Proveedor>
  deleteProveedor: (id: string) => Promise<void>
  clearError: () => void
  clearSelected: () => void
}

export const useProveedorStore = create<ProveedorState>((set, get) => ({
  proveedores: [],
  totalProveedores: 0,
  selectedProveedor: null,
  historial: { items: [], total: 0 },
  loading: false,
  error: null,
  searchQuery: '',
  skip: 0,
  limit: 20,
  incluirInactivos: false,

  setSearchQuery: (q: string) => {
    set({ searchQuery: q, skip: 0 })
    get().fetchProveedores()
  },

  setSkip: (skip: number) => {
    set({ skip })
    get().fetchProveedores()
  },

  setLimit: (limit: number) => {
    set({ limit, skip: 0 })
    get().fetchProveedores()
  },

  setIncluirInactivos: (v: boolean) => {
    set({ incluirInactivos: v, skip: 0 })
    get().fetchProveedores()
  },

  fetchProveedores: async () => {
    set({ loading: true, error: null })
    try {
      const { searchQuery, skip, limit, incluirInactivos } = get()
      const response = await fetchProveedores({
        nombre: searchQuery || undefined,
        skip,
        limit,
        incluir_inactivos: incluirInactivos,
      })
      set({
        proveedores: response.items,
        totalProveedores: response.total,
        loading: false,
      })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar proveedores'
      set({ error: msg, loading: false })
    }
  },

  fetchProveedor: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const proveedor = await fetchProveedor(id)
      set({ selectedProveedor: proveedor, loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar proveedor'
      set({ error: msg, loading: false })
    }
  },

  fetchHistorial: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const response = await fetchProveedorHistorial(id)
      set({ historial: { items: response.items, total: response.total }, loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar historial'
      set({ error: msg, loading: false })
    }
  },

  createProveedor: async (dto: ProveedorCreate) => {
    set({ loading: true, error: null })
    try {
      const proveedor = await createProveedor(dto)
      set({
        proveedores: [proveedor, ...get().proveedores],
        totalProveedores: get().totalProveedores + 1,
        loading: false,
      })
      return proveedor
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al crear proveedor'
      set({ error: msg, loading: false })
      throw err
    }
  },

  updateProveedor: async (id: string, dto: ProveedorUpdate) => {
    set({ loading: true, error: null })
    try {
      const proveedor = await updateProveedor(id, dto)
      set({
        proveedores: get().proveedores.map((p) => (p.id === id ? proveedor : p)),
        selectedProveedor: get().selectedProveedor?.id === id ? proveedor : get().selectedProveedor,
        loading: false,
      })
      return proveedor
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al actualizar proveedor'
      set({ error: msg, loading: false })
      throw err
    }
  },

  deleteProveedor: async (id: string) => {
    set({ loading: true, error: null })
    try {
      await deleteProveedor(id)
      set({
        proveedores: get().proveedores.map((p) => (p.id === id ? { ...p, activo: false } as Proveedor : p)),
        selectedProveedor: get().selectedProveedor?.id === id ? { ...get().selectedProveedor, activo: false } as Proveedor : get().selectedProveedor,
        loading: false,
      })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al desactivar proveedor'
      set({ error: msg, loading: false })
      throw err
    }
  },

  clearError: () => set({ error: null }),
  clearSelected: () => set({ selectedProveedor: null, historial: { items: [], total: 0 } }),
}))
