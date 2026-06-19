import { create } from 'zustand'
import axios from 'axios'
import type {
  StockItem,
  MovimientoStock,
  AlertaStockItem,
  AjusteStockPayload,
  PaginatedStockResponse,
  PaginatedKardexResponse,
} from '@/shared/types/stock'

interface StockState {
  stock: StockItem[]
  kardex: MovimientoStock[]
  alertas: AlertaStockItem[]
  totalStock: number
  totalKardex: number
  loading: boolean
  error: string | null
  fetchStock: (params?: { skip?: number; limit?: number }) => Promise<void>
  fetchKardex: (productoId: string, params?: { skip?: number; limit?: number }) => Promise<void>
  fetchAlertas: () => Promise<void>
  ajustarStock: (payload: AjusteStockPayload) => Promise<MovimientoStock>
  clearError: () => void
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const useStockStore = create<StockState>((set) => ({
  stock: [],
  kardex: [],
  alertas: [],
  totalStock: 0,
  totalKardex: 0,
  loading: false,
  error: null,

  fetchStock: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const query = new URLSearchParams()
      if (params.skip !== undefined) query.set('skip', String(params.skip))
      if (params.limit !== undefined) query.set('limit', String(params.limit))

      const response = await api.get<PaginatedStockResponse>(`/stock?${query.toString()}`)
      set({ stock: response.data.items, totalStock: response.data.total, loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar stock'
      set({ error: msg, loading: false })
    }
  },

  fetchKardex: async (productoId: string, params = {}) => {
    set({ loading: true, error: null })
    try {
      const query = new URLSearchParams()
      if (params.skip !== undefined) query.set('skip', String(params.skip))
      if (params.limit !== undefined) query.set('limit', String(params.limit))

      const response = await api.get<PaginatedKardexResponse>(`/stock/movimientos/${productoId}?${query.toString()}`)
      set({ kardex: response.data.items, totalKardex: response.data.total, loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar kardex'
      set({ error: msg, loading: false })
    }
  },

  fetchAlertas: async () => {
    set({ loading: true, error: null })
    try {
      const response = await api.get<AlertaStockItem[]>('/stock/alertas')
      set({ alertas: response.data, loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar alertas'
      set({ error: msg, loading: false })
    }
  },

  ajustarStock: async (payload: AjusteStockPayload) => {
    set({ loading: true, error: null })
    try {
      const response = await api.post<MovimientoStock>('/stock/ajustes', payload)
      const movimiento = response.data
      set({ loading: false })
      return movimiento
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al ajustar stock'
      set({ error: msg, loading: false })
      throw err
    }
  },

  clearError: () => set({ error: null }),
}))
