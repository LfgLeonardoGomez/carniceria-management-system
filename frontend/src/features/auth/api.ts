import axios from 'axios'
import type { User } from '@/store/authStore'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface LoginRequest {
  email: string
  contrasena: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  usuario: User
}

export interface RecoverRequest {
  email: string
}

export interface ResetRequest {
  token: string
  new_password: string
}

export async function login(dto: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>('/auth/login', dto)
  return response.data
}

export async function recover(dto: RecoverRequest): Promise<void> {
  await api.post('/auth/recover', dto)
}

export async function reset(dto: ResetRequest): Promise<void> {
  await api.post('/auth/reset', dto)
}
