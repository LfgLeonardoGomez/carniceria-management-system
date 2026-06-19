import { create } from 'zustand'
import type { Cliente, ClienteCreate, ClienteUpdate } from '@/shared/types/cliente'
import {
  fetchClientes,
  fetchCliente,
  createCliente,
  updateCliente,
  deleteCliente,
  fetchClienteHistorial,
} from '@/features/clientes/api'

interface ClienteState {
  clientes: Cliente[]
  totalClientes: number
  selectedCliente: Cliente | null
  historial: { items: unknown[]; total: number }
  loading: boolean
  error: string | null
  tipoFilter: string
  searchQuery: string
  skip: number
  limit: number
  setTipoFilter: (tipo: string) => void
  setSearchQuery: (q: string) => void
  setSkip: (skip: number) => void
  setLimit: (limit: number) => void
  fetchClientes: () => Promise<void>
  fetchCliente: (id: string) => Promise<void>
  fetchHistorial: (id: string) => Promise<void>
  createCliente: (dto: ClienteCreate) => Promise<Cliente>
  updateCliente: (id: string, dto: ClienteUpdate) => Promise<Cliente>
  deleteCliente: (id: string) => Promise<Cliente>
  clearError: () => void
  clearSelected: () => void
}

export const useClienteStore = create<ClienteState>((set, get) => ({
  clientes: [],
  totalClientes: 0,
  selectedCliente: null,
  historial: { items: [], total: 0 },
  loading: false,
  error: null,
  tipoFilter: '',
  searchQuery: '',
  skip: 0,
  limit: 20,

  setTipoFilter: (tipo: string) => {
    set({ tipoFilter: tipo, skip: 0 })
    get().fetchClientes()
  },

  setSearchQuery: (q: string) => {
    set({ searchQuery: q, skip: 0 })
    get().fetchClientes()
  },

  setSkip: (skip: number) => {
    set({ skip })
    get().fetchClientes()
  },

  setLimit: (limit: number) => {
    set({ limit, skip: 0 })
    get().fetchClientes()
  },

  fetchClientes: async () => {
    set({ loading: true, error: null })
    try {
      const { searchQuery, tipoFilter, skip, limit } = get()
      const response = await fetchClientes({
        search: searchQuery || undefined,
        tipo_cliente: tipoFilter || undefined,
        skip,
        limit,
      })
      set({
        clientes: response.items,
        totalClientes: response.total,
        loading: false,
      })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar clientes'
      set({ error: msg, loading: false })
    }
  },

  fetchCliente: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const cliente = await fetchCliente(id)
      set({ selectedCliente: cliente, loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar cliente'
      set({ error: msg, loading: false })
    }
  },

  fetchHistorial: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const response = await fetchClienteHistorial(id)
      set({ historial: { items: response.items, total: response.total }, loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar historial'
      set({ error: msg, loading: false })
    }
  },

  createCliente: async (dto: ClienteCreate) => {
    set({ loading: true, error: null })
    try {
      const cliente = await createCliente(dto)
      set({
        clientes: [cliente, ...get().clientes],
        totalClientes: get().totalClientes + 1,
        loading: false,
      })
      return cliente
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al crear cliente'
      set({ error: msg, loading: false })
      throw err
    }
  },

  updateCliente: async (id: string, dto: ClienteUpdate) => {
    set({ loading: true, error: null })
    try {
      const cliente = await updateCliente(id, dto)
      set({
        clientes: get().clientes.map((c) => (c.id === id ? cliente : c)),
        selectedCliente: get().selectedCliente?.id === id ? cliente : get().selectedCliente,
        loading: false,
      })
      return cliente
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al actualizar cliente'
      set({ error: msg, loading: false })
      throw err
    }
  },

  deleteCliente: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const cliente = await deleteCliente(id)
      set({
        clientes: get().clientes.map((c) => (c.id === id ? cliente : c)),
        selectedCliente: get().selectedCliente?.id === id ? cliente : get().selectedCliente,
        loading: false,
      })
      return cliente
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al desactivar cliente'
      set({ error: msg, loading: false })
      throw err
    }
  },

  clearError: () => set({ error: null }),
  clearSelected: () => set({ selectedCliente: null, historial: { items: [], total: 0 } }),
}))
