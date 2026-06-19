import { create } from 'zustand'
import axios from 'axios'
import type {
  Producto,
  ProductoCreate,
  ProductoUpdate,
  CategoriaProducto,
  PaginatedProductoResponse,
  ImportPreview,
  ImportConfirmResult,
} from '@/shared/types/producto'

interface ProductoState {
  productos: Producto[]
  categorias: CategoriaProducto[]
  totalProductos: number
  loading: boolean
  error: string | null
  importPreview: ImportPreview | null
  fetchProductos: (params?: { search?: string; categoriaId?: string; activo?: boolean; skip?: number; limit?: number }) => Promise<void>
  fetchCategorias: () => Promise<void>
  createProducto: (dto: ProductoCreate) => Promise<Producto>
  updateProducto: (id: string, dto: ProductoUpdate) => Promise<Producto>
  toggleProductoActivo: (id: string, activo: boolean) => Promise<Producto>
  createCategoria: (nombre: string) => Promise<CategoriaProducto>
  updateCategoria: (id: string, nombre: string) => Promise<CategoriaProducto>
  deleteCategoria: (id: string) => Promise<void>
  uploadImport: (file: File) => Promise<ImportPreview>
  confirmImport: (sessionId: string) => Promise<ImportConfirmResult>
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

export const useProductoStore = create<ProductoState>((set, get) => ({
  productos: [],
  categorias: [],
  totalProductos: 0,
  loading: false,
  error: null,
  importPreview: null,

  fetchProductos: async (params = {}) => {
    set({ loading: true, error: null })
    try {
      const query = new URLSearchParams()
      if (params.search) query.set('search', params.search)
      if (params.categoriaId) query.set('categoria_id', params.categoriaId)
      if (params.activo !== undefined) query.set('activo', String(params.activo))
      if (params.skip !== undefined) query.set('skip', String(params.skip))
      if (params.limit !== undefined) query.set('limit', String(params.limit))

      const response = await api.get<PaginatedProductoResponse>(`/producto?${query.toString()}`)
      set({ productos: response.data.items, totalProductos: response.data.total, loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar productos'
      set({ error: msg, loading: false })
    }
  },

  fetchCategorias: async () => {
    set({ loading: true, error: null })
    try {
      const response = await api.get<{ items: CategoriaProducto[]; total: number }>('/producto/categorias')
      set({ categorias: response.data.items, loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cargar categorías'
      set({ error: msg, loading: false })
    }
  },

  createProducto: async (dto: ProductoCreate) => {
    set({ loading: true, error: null })
    try {
      const response = await api.post<Producto>('/producto', dto)
      const current = get().productos
      set({ productos: [response.data, ...current], totalProductos: get().totalProductos + 1, loading: false })
      return response.data
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al crear producto'
      set({ error: msg, loading: false })
      throw err
    }
  },

  updateProducto: async (id: string, dto: ProductoUpdate) => {
    set({ loading: true, error: null })
    try {
      const response = await api.put<Producto>(`/producto/${id}`, dto)
      const updated = response.data
      set({
        productos: get().productos.map((p) => (p.id === id ? updated : p)),
        loading: false,
      })
      return updated
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al actualizar producto'
      set({ error: msg, loading: false })
      throw err
    }
  },

  toggleProductoActivo: async (id: string, activo: boolean) => {
    set({ loading: true, error: null })
    try {
      const response = await api.patch<Producto>(`/producto/${id}/activo`, { activo })
      const updated = response.data
      set({
        productos: get().productos.map((p) => (p.id === id ? updated : p)),
        loading: false,
      })
      return updated
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al cambiar estado'
      set({ error: msg, loading: false })
      throw err
    }
  },

  createCategoria: async (nombre: string) => {
    set({ loading: true, error: null })
    try {
      const response = await api.post<CategoriaProducto>('/producto/categorias', { nombre })
      set({ categorias: [...get().categorias, response.data], loading: false })
      return response.data
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al crear categoría'
      set({ error: msg, loading: false })
      throw err
    }
  },

  updateCategoria: async (id: string, nombre: string) => {
    set({ loading: true, error: null })
    try {
      const response = await api.put<CategoriaProducto>(`/producto/categorias/${id}`, { nombre })
      const updated = response.data
      set({
        categorias: get().categorias.map((c) => (c.id === id ? updated : c)),
        loading: false,
      })
      return updated
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al actualizar categoría'
      set({ error: msg, loading: false })
      throw err
    }
  },

  deleteCategoria: async (id: string) => {
    set({ loading: true, error: null })
    try {
      await api.delete(`/producto/categorias/${id}`)
      set({ categorias: get().categorias.filter((c) => c.id !== id), loading: false })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al eliminar categoría'
      set({ error: msg, loading: false })
      throw err
    }
  },

  uploadImport: async (file: File) => {
    set({ loading: true, error: null })
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await api.post<ImportPreview>('/producto/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      set({ importPreview: response.data, loading: false })
      return response.data
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al procesar archivo'
      set({ error: msg, loading: false })
      throw err
    }
  },

  confirmImport: async (sessionId: string) => {
    set({ loading: true, error: null })
    try {
      const response = await api.post<ImportConfirmResult>(`/producto/import/confirm?session_id=${sessionId}`)
      set({ importPreview: null, loading: false })
      return response.data
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Error al confirmar importación'
      set({ error: msg, loading: false })
      throw err
    }
  },

  clearError: () => set({ error: null }),
}))
