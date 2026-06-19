import axios from 'axios'
import type { Producto } from '@/shared/types/producto'

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

export async function buscarProductoPorPlu(plu: string): Promise<Producto> {
  const response = await api.get<Producto>(`/productos?plu=${plu}`)
  return response.data
}
