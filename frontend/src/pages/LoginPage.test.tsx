import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { LoginPage } from '@/pages/LoginPage'
import * as api from '@/features/auth/api'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock('@/features/auth/api')

const mockSetToken = vi.fn()
const mockSetUser = vi.fn()

const mockAuthStoreState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isImpersonating: false,
  setUser: mockSetUser,
  setToken: mockSetToken,
  setImpersonating: vi.fn(),
  logout: vi.fn(),
}

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => mockAuthStoreState,
}))

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<div>Dashboard</div>} />
        <Route path="/recuperar-contrasena" element={<div>Recuperar</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

// ---------------------------------------------------------------------------
// Task 1.4 — LoginPage tests
// ---------------------------------------------------------------------------
describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders email and password fields', () => {
    renderLogin()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
  })

  it('submits credentials and redirects on success', async () => {
    const mockResponse = {
      access_token: 'fake-token-123',
      token_type: 'bearer',
    }
    vi.mocked(api.login).mockResolvedValue(mockResponse)

    renderLogin()

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith({ email: 'user@example.com', password: 'password123' })
    })

    await waitFor(() => {
      expect(localStorage.getItem('access_token')).toBe('fake-token-123')
    })

    expect(mockSetToken).toHaveBeenCalledWith('fake-token-123')
    expect(mockSetUser).toHaveBeenCalledWith(mockResponse)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('shows generic error on invalid credentials', async () => {
    const error = new Error('Invalid credentials') as Error & { response?: { data: { detail: string } } }
    error.response = { data: { detail: 'Credenciales inválidas' } }
    vi.mocked(api.login).mockRejectedValue(error)

    renderLogin()

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'wrongpass' } })
    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(screen.getByText('Credenciales inválidas')).toBeInTheDocument()
    })
  })

  it('shows inactive account message', async () => {
    const error = new Error('Inactive') as Error & { response?: { data: { detail: string } } }
    error.response = { data: { detail: 'Cuenta inactiva' } }
    vi.mocked(api.login).mockRejectedValue(error)

    renderLogin()

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'inactive@example.com' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(screen.getByText('Cuenta inactiva')).toBeInTheDocument()
    })
  })

  it('shows generic message for network errors', async () => {
    vi.mocked(api.login).mockRejectedValue(new Error('Network Error'))

    renderLogin()

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(screen.getByText(/error al iniciar sesión/i)).toBeInTheDocument()
    })
  })

  it('navigates to password recovery page', () => {
    renderLogin()
    fireEvent.click(screen.getByText(/¿olvidaste tu contraseña\?/i))
    expect(screen.getByText('Recuperar')).toBeInTheDocument()
  })
})
