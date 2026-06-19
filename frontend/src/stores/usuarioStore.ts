import { create } from 'zustand'
import * as usuarioService from '@/shared/services/usuarioService'
import type {
  UsuarioCreate,
  UsuarioUpdate,
  UsuarioPublic,
  PerfilPublic,
  PerfilUpdate,
} from '@/shared/types/usuario'

export type { UsuarioCreate, UsuarioUpdate, UsuarioPublic, PerfilPublic, PerfilUpdate }
export { ROLES } from '@/shared/types/usuario'

interface UsuarioState {
  usuarios: UsuarioPublic[]
  total: number
  loading: boolean
  error: string | null
  tempPassword: string | null
  skip: number
  limit: number
  activoFilter: boolean | null
  rolFilter: string | null
  perfil: PerfilPublic | null
  fetchUsuarios: (skip?: number, limit?: number, activo?: boolean | null, rol?: string | null) => Promise<void>
  createUsuario: (dto: UsuarioCreate) => Promise<string>
  updateUsuario: (id: string, dto: UsuarioUpdate) => Promise<void>
  deactivateUsuario: (id: string) => Promise<void>
  reactivateUsuario: (id: string) => Promise<void>
  fetchPerfil: () => Promise<void>
  updatePerfil: (dto: PerfilUpdate) => Promise<void>
  changePassword: (dto: { contrasena_actual: string; contrasena_nueva: string }) => Promise<void>
  clearTempPassword: () => void
  clearError: () => void
}

export const useUsuarioStore = create<UsuarioState>((set) => ({
  usuarios: [],
  total: 0,
  loading: false,
  error: null,
  tempPassword: null,
  skip: 0,
  limit: 20,
  activoFilter: null,
  rolFilter: null,
  perfil: null,

  fetchUsuarios: async (skip = 0, limit = 20, activo = null, rol = null) => {
    set({ loading: true, error: null, skip, limit, activoFilter: activo, rolFilter: rol })
    try {
      const data = await usuarioService.listarUsuarios(skip, limit, activo)
      // Client-side rol filter since backend doesn't support it yet
      let items = data.items
      if (rol) {
        items = items.filter((u) => u.rol === rol)
      }
      set({ usuarios: items, total: data.total, loading: false })
    } catch (err: unknown) {
      set({ error: usuarioService.extractErrorMessage(err), loading: false })
      throw err
    }
  },

  createUsuario: async (dto: UsuarioCreate) => {
    set({ loading: true, error: null, tempPassword: null })
    try {
      const data = await usuarioService.crearUsuario(dto)
      set({ tempPassword: data.contrasena_temporal, loading: false })
      return data.contrasena_temporal
    } catch (err: unknown) {
      set({ error: usuarioService.extractErrorMessage(err), loading: false })
      throw err
    }
  },

  updateUsuario: async (id: string, dto: UsuarioUpdate) => {
    set({ loading: true, error: null })
    try {
      const updated = await usuarioService.actualizarUsuario(id, dto)
      set((state) => ({
        usuarios: state.usuarios.map((u) => (u.id === id ? updated : u)),
        loading: false,
      }))
    } catch (err: unknown) {
      set({ error: usuarioService.extractErrorMessage(err), loading: false })
      throw err
    }
  },

  deactivateUsuario: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const updated = await usuarioService.desactivarUsuario(id)
      set((state) => ({
        usuarios: state.usuarios.map((u) => (u.id === id ? updated : u)),
        loading: false,
      }))
    } catch (err: unknown) {
      set({ error: usuarioService.extractErrorMessage(err), loading: false })
      throw err
    }
  },

  reactivateUsuario: async (id: string) => {
    set({ loading: true, error: null })
    try {
      const updated = await usuarioService.reactivarUsuario(id)
      set((state) => ({
        usuarios: state.usuarios.map((u) => (u.id === id ? updated : u)),
        loading: false,
      }))
    } catch (err: unknown) {
      set({ error: usuarioService.extractErrorMessage(err), loading: false })
      throw err
    }
  },

  fetchPerfil: async () => {
    set({ loading: true, error: null })
    try {
      const data = await usuarioService.obtenerPerfil()
      set({ perfil: data, loading: false })
    } catch (err: unknown) {
      set({ error: usuarioService.extractErrorMessage(err), loading: false })
      throw err
    }
  },

  updatePerfil: async (dto: PerfilUpdate) => {
    set({ loading: true, error: null })
    try {
      const data = await usuarioService.actualizarPerfil(dto)
      set({ perfil: data, loading: false })
    } catch (err: unknown) {
      set({ error: usuarioService.extractErrorMessage(err), loading: false })
      throw err
    }
  },

  changePassword: async (dto: { contrasena_actual: string; contrasena_nueva: string }) => {
    set({ loading: true, error: null })
    try {
      await usuarioService.cambiarContrasena(dto)
      set({ loading: false })
    } catch (err: unknown) {
      set({ error: usuarioService.extractErrorMessage(err), loading: false })
      throw err
    }
  },

  clearTempPassword: () => set({ tempPassword: null }),
  clearError: () => set({ error: null }),
}))
