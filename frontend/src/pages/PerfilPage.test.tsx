import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PerfilPage } from '@/pages/PerfilPage'

const mockFetchPerfil = vi.fn().mockResolvedValue(undefined)
const mockUpdatePerfil = vi.fn().mockResolvedValue(undefined)
const mockChangePassword = vi.fn().mockResolvedValue(undefined)
const mockClearError = vi.fn()

const mockPerfil = {
  id: 'u-1',
  nombre: 'Carlos',
  apellido: 'López',
  email: 'carlos@example.com',
  rol: 'Administrador',
  empresa: 'Carnicería Don Juan',
}

const mockUsuarioStoreState = {
  perfil: mockPerfil,
  loading: false,
  error: null,
  fetchPerfil: mockFetchPerfil,
  updatePerfil: mockUpdatePerfil,
  changePassword: mockChangePassword,
  clearError: mockClearError,
}

const mockUseUsuarioStore = vi.fn(() => mockUsuarioStoreState)

const mockUser = { id: 'u-1', email: 'carlos@example.com', nombre: 'Carlos', apellido: 'López', rol: 'Administrador' }

const mockAuthStoreState = {
  user: mockUser,
  isAuthenticated: true,
  setUser: vi.fn(),
}

const mockUseAuthStore = vi.fn(() => mockAuthStoreState)

vi.mock('@/stores/usuarioStore', () => ({
  useUsuarioStore: () => mockUseUsuarioStore(),
}))

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => mockUseAuthStore(),
}))

describe('PerfilPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders profile form with data', () => {
    render(
      <MemoryRouter>
        <PerfilPage />
      </MemoryRouter>
    )

    expect(screen.getByLabelText('Nombre')).toHaveValue('Carlos')
    expect(screen.getByLabelText('Apellido')).toHaveValue('López')
    expect(screen.getByLabelText('Email')).toHaveValue('carlos@example.com')
    expect(screen.getByLabelText('Rol')).toHaveValue('Administrador')
    expect(screen.getByLabelText('Empresa')).toHaveValue('Carnicería Don Juan')
  })

  it('submits profile update', async () => {
    render(
      <MemoryRouter>
        <PerfilPage />
      </MemoryRouter>
    )

    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Carlos Andrés' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }))

    await waitFor(() => {
      expect(mockUpdatePerfil).toHaveBeenCalledWith({
        nombre: 'Carlos Andrés',
        apellido: 'López',
        email: 'carlos@example.com',
      })
    })
  })

  it('validates password confirmation mismatch', async () => {
    render(
      <MemoryRouter>
        <PerfilPage />
      </MemoryRouter>
    )

    fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'oldpass' } })
    fireEvent.change(screen.getByLabelText('Contraseña nueva'), { target: { value: 'newpass' } })
    fireEvent.change(screen.getByLabelText('Confirmar contraseña nueva'), { target: { value: 'different' } })
    fireEvent.click(screen.getByRole('button', { name: /cambiar contraseña/i }))

    await waitFor(() => {
      expect(screen.getByText('Las contraseñas no coinciden')).toBeInTheDocument()
    })
    expect(mockChangePassword).not.toHaveBeenCalled()
  })

  it('validates new password length', async () => {
    render(
      <MemoryRouter>
        <PerfilPage />
      </MemoryRouter>
    )

    fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'oldpass' } })
    fireEvent.change(screen.getByLabelText('Contraseña nueva'), { target: { value: '123' } })
    fireEvent.change(screen.getByLabelText('Confirmar contraseña nueva'), { target: { value: '123' } })
    fireEvent.click(screen.getByRole('button', { name: /cambiar contraseña/i }))

    await waitFor(() => {
      expect(screen.getByText('La contraseña nueva debe tener al menos 6 caracteres')).toBeInTheDocument()
    })
    expect(mockChangePassword).not.toHaveBeenCalled()
  })

  it('submits password change when valid', async () => {
    render(
      <MemoryRouter>
        <PerfilPage />
      </MemoryRouter>
    )

    fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'oldpass' } })
    fireEvent.change(screen.getByLabelText('Contraseña nueva'), { target: { value: 'newsecurepassword' } })
    fireEvent.change(screen.getByLabelText('Confirmar contraseña nueva'), { target: { value: 'newsecurepassword' } })
    fireEvent.click(screen.getByRole('button', { name: /cambiar contraseña/i }))

    await waitFor(() => {
      expect(mockChangePassword).toHaveBeenCalledWith({
        contrasena_actual: 'oldpass',
        contrasena_nueva: 'newsecurepassword',
      })
    })
  })
})
