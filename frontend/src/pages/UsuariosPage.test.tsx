import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { UsuariosPage } from '@/pages/UsuariosPage'

const mockFetchUsuarios = vi.fn().mockResolvedValue(undefined)
const mockCreateUsuario = vi.fn().mockResolvedValue('temp123')
const mockUpdateUsuario = vi.fn().mockResolvedValue(undefined)
const mockDeactivateUsuario = vi.fn().mockResolvedValue(undefined)
const mockReactivateUsuario = vi.fn().mockResolvedValue(undefined)
const mockClearTempPassword = vi.fn()
const mockClearError = vi.fn()

const mockUsuarios = [
  {
    id: 'u-1',
    nombre: 'María',
    apellido: 'Gómez',
    email: 'maria@example.com',
    rol: 'Administrador',
    activo: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'u-2',
    nombre: 'Pedro',
    apellido: 'Ruiz',
    email: 'pedro@example.com',
    rol: 'Cajero',
    activo: false,
    created_at: '2024-02-01T00:00:00Z',
    updated_at: '2024-02-01T00:00:00Z',
  },
]

const mockUsuarioStoreState = {
  usuarios: mockUsuarios,
  total: 2,
  loading: false,
  error: null,
  tempPassword: null,
  skip: 0,
  limit: 20,
  activoFilter: null,
  rolFilter: null,
  fetchUsuarios: mockFetchUsuarios,
  createUsuario: mockCreateUsuario,
  updateUsuario: mockUpdateUsuario,
  deactivateUsuario: mockDeactivateUsuario,
  reactivateUsuario: mockReactivateUsuario,
  clearTempPassword: mockClearTempPassword,
  clearError: mockClearError,
}

const mockUseUsuarioStore = vi.fn(() => mockUsuarioStoreState)

const mockUser = { id: 'u-1', email: 'maria@example.com', nombre: 'María', apellido: 'Gómez', rol: 'Administrador' }

const mockAuthStoreState = {
  user: mockUser,
  isAuthenticated: true,
}

const mockUseAuthStore = vi.fn(() => mockAuthStoreState)

vi.mock('@/stores/usuarioStore', () => ({
  useUsuarioStore: () => mockUseUsuarioStore(),
}))

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => mockUseAuthStore(),
}))

vi.mock('@/components/UsuarioCreateModal', () => ({
  UsuarioCreateModal: () => <div data-testid="create-modal" />,
}))
vi.mock('@/components/UsuarioEditModal', () => ({
  UsuarioEditModal: () => <div data-testid="edit-modal" />,
}))

describe('UsuariosPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders user grid with data', () => {
    render(
      <MemoryRouter>
        <UsuariosPage />
      </MemoryRouter>
    )

    expect(screen.getByText('María Gómez')).toBeInTheDocument()
    expect(screen.getByText('maria@example.com')).toBeInTheDocument()
    expect(screen.getByText('Pedro Ruiz')).toBeInTheDocument()
    expect(screen.getByText('pedro@example.com')).toBeInTheDocument()
  })

  it('opens create modal when clicking new user button', () => {
    render(
      <MemoryRouter>
        <UsuariosPage />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /nuevo usuario/i }))
    expect(screen.getByTestId('create-modal')).toBeInTheDocument()
  })

  it('shows reactivar button for inactive user', () => {
    render(
      <MemoryRouter>
        <UsuariosPage />
      </MemoryRouter>
    )

    const reactivarButtons = screen.getAllByRole('button', { name: /reactivar/i })
    expect(reactivarButtons.length).toBeGreaterThan(0)
  })

  it('calls reactivateUsuario when reactivar clicked', async () => {
    render(
      <MemoryRouter>
        <UsuariosPage />
      </MemoryRouter>
    )

    fireEvent.click(screen.getByRole('button', { name: /reactivar/i }))
    await waitFor(() => {
      expect(mockReactivateUsuario).toHaveBeenCalledWith('u-2')
    })
  })

  it('filters by estado', () => {
    render(
      <MemoryRouter>
        <UsuariosPage />
      </MemoryRouter>
    )

    const estadoSelect = screen.getByLabelText('Estado:')
    fireEvent.change(estadoSelect, { target: { value: 'true' } })

    expect(mockFetchUsuarios).toHaveBeenCalledWith(0, 20, true, null)
  })

  it('filters by rol', () => {
    render(
      <MemoryRouter>
        <UsuariosPage />
      </MemoryRouter>
    )

    const rolSelect = screen.getByLabelText('Rol:')
    fireEvent.change(rolSelect, { target: { value: 'Administrador' } })

    expect(mockFetchUsuarios).toHaveBeenCalledWith(0, 20, null, 'Administrador')
  })
})
