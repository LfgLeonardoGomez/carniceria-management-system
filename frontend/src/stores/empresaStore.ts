import { create } from 'zustand'
import axios from 'axios'
import type { EmpresaPublic, EmpresaUpdate } from '@/shared/types/empresa'

interface EmpresaState {
  empresa: EmpresaPublic | null
  loading: boolean
  error: string | null
  fetchEmpresa: () => Promise<void>
  updateEmpresa: (dto: EmpresaUpdate) => Promise<void>
  uploadLogo: (file: File) => Promise<void>
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

export const useEmpresaStore = create<EmpresaState>((set, get) => ({
  empresa: null,
  loading: false,
  error: null,

  fetchEmpresa: async () => {
    set({ loading: true, error: null })
    try {
      const response = await api.get<EmpresaPublic>('/empresas/me')
      set({ empresa: response.data, loading: false })
    } catch (err: any) {
      set({ error: err.response?.data?.detail || 'Error al cargar empresa', loading: false })
    }
  },

  updateEmpresa: async (dto: EmpresaUpdate) => {
    set({ loading: true, error: null })
    try {
      const response = await api.put<EmpresaPublic>('/empresas/me', dto)
      set({ empresa: response.data, loading: false })
    } catch (err: any) {
      set({ error: err.response?.data?.detail || 'Error al actualizar empresa', loading: false })
      throw err
    }
  },

  uploadLogo: async (file: File) => {
    set({ loading: true, error: null })
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await api.post<{ logo_url: string; filename: string; content_type: string }>('/empresas/me/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const current = get().empresa
      if (current) {
        set({ empresa: { ...current, logo_url: response.data.logo_url }, loading: false })
      }
    } catch (err: any) {
      set({ error: err.response?.data?.detail || 'Error al subir logo', loading: false })
      throw err
    }
  },
}))
