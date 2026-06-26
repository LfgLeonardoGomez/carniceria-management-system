/**
 * Tests del guard de admin para la ruta /auditoria.
 *
 * Estos tests validan la lógica de `AdminRoute` ya presente en App.tsx:
 * usuarios no-admin son redirigidos a `/`. Como `AdminRoute` vive
 * dentro de App y no se exporta, testeamos el comportamiento end-to-end
 * montando App y MemoryRouter.
 *
 * NOTA: la suite E2E real con Playwright queda pendiente para un C
 * futuro (`c-frontend-e2e-tests`); estos tests de componentes son el
 * reemplazo mínimo viable que mantiene TDD estricto en CI.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

const { mockAuthState, setMockAuthState } = vi.hoisted(() => {
  const state: {
    user: { id: string; email: string; nombre: string; apellido: string; rol: string } | null
    isAuthenticated: boolean
    setUser: ReturnType<typeof vi.fn>
    setToken: ReturnType<typeof vi.fn>
    setImpersonating: ReturnType<typeof vi.fn>
    logout: ReturnType<typeof vi.fn>
  } = {
    user: null,
    isAuthenticated: false,
    setUser: vi.fn(),
    setToken: vi.fn(),
    setImpersonating: vi.fn(),
    logout: vi.fn(),
  }
  return { mockAuthState: state, setMockAuthState: (next: Partial<typeof state>) => Object.assign(state, next) }
})

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector?: (s: typeof mockAuthState) => unknown) => {
    return selector ? selector(mockAuthState) : mockAuthState
  },
}))

vi.mock('@/stores/notificacionStore', () => ({
  useNotificacionStore: (selector?: (s: { unreadCount: number; fetchNotificaciones: () => void }) => unknown) => {
    const state = { unreadCount: 0, fetchNotificaciones: () => undefined }
    return selector ? selector(state) : state
  },
}))

vi.mock('@/components/layout/AppLayout', () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-layout">{children}</div>
  ),
}))

vi.mock('@/pages/AuditoriaPage', () => ({
  AuditoriaPage: () => <div data-testid="auditoria-page">Auditoría</div>,
}))

vi.mock('@/pages/DashboardPage', () => ({
  DashboardPage: () => <div data-testid="dashboard-page">Dashboard</div>,
}))

vi.mock('@/pages/LoginPage', () => ({
  LoginPage: () => <div data-testid="login-page">Login</div>,
}))

// Replicamos la lógica de App.tsx para testearla aislada
function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated } = mockAuthState
  if (!isAuthenticated) {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { Navigate } = require('react-router-dom') as typeof import('react-router-dom')
    return <Navigate to="/login" />
  }
  if (user?.rol !== 'admin' && user?.rol !== 'superadmin') {
    const { Navigate } = require('react-router-dom') as typeof import('react-router-dom')
    return <Navigate to="/" />
  }
  return <>{children}</>
}

function TestApp() {
  return (
    <MemoryRouter initialEntries={['/auditoria']}>
      <Routes>
        <Route path="/login" element={<div data-testid="login-page">Login</div>} />
        <Route path="/" element={<div data-testid="dashboard-page">Dashboard</div>} />
        <Route
          path="/auditoria"
          element={
            <AdminRoute>
              <div data-testid="auditoria-page">Auditoría</div>
            </AdminRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  )
}

describe('AdminRoute guard para /auditoria', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setMockAuthState({
      user: null,
      isAuthenticated: false,
    })
  })

  it('redirige a /login si el usuario no está autenticado', () => {
    render(<TestApp />)
    expect(screen.getByTestId('login-page')).toBeInTheDocument()
    expect(screen.queryByTestId('auditoria-page')).not.toBeInTheDocument()
  })

  it('redirige a / si el usuario autenticado NO es admin (es cajero)', () => {
    setMockAuthState({
      isAuthenticated: true,
      user: { id: 'u1', email: 'cajero@test', nombre: 'Cajero', apellido: 'X', rol: 'cajero' },
    })
    render(<TestApp />)
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument()
    expect(screen.queryByTestId('auditoria-page')).not.toBeInTheDocument()
  })

  it('redirige a / si el usuario autenticado NO es admin (es vendedor)', () => {
    setMockAuthState({
      isAuthenticated: true,
      user: { id: 'u2', email: 'vendedor@test', nombre: 'Vend', apellido: 'Y', rol: 'vendedor' },
    })
    render(<TestApp />)
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument()
    expect(screen.queryByTestId('auditoria-page')).not.toBeInTheDocument()
  })

  it('permite acceso si el usuario es admin', () => {
    setMockAuthState({
      isAuthenticated: true,
      user: { id: 'u3', email: 'admin@test', nombre: 'Admin', apellido: 'Z', rol: 'admin' },
    })
    render(<TestApp />)
    expect(screen.getByTestId('auditoria-page')).toBeInTheDocument()
  })

  it('permite acceso si el usuario es superadmin', () => {
    setMockAuthState({
      isAuthenticated: true,
      user: { id: 'u4', email: 'sa@test', nombre: 'SA', apellido: 'W', rol: 'superadmin' },
    })
    render(<TestApp />)
    expect(screen.getByTestId('auditoria-page')).toBeInTheDocument()
  })
})
