import axios from 'axios'
import type {
  GraficosResponse,
  IndicadoresResponse,
  RankingsResponse,
} from '@/shared/types/dashboard'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function fetchIndicadores(): Promise<IndicadoresResponse> {
  const response = await api.get<IndicadoresResponse>('/dashboard/indicadores')
  return response.data
}

export async function fetchRankings(top = 10): Promise<RankingsResponse> {
  const response = await api.get<RankingsResponse>('/dashboard/rankings', {
    params: { top },
  })
  return response.data
}

export async function fetchGraficos(): Promise<GraficosResponse> {
  const response = await api.get<GraficosResponse>('/dashboard/graficos')
  return response.data
}
