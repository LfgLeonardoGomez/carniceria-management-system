/**
 * Test de integración que simula el flujo end-to-end del panel de
 * notificaciones dentro del Header.
 *
 * NOTA: la suite E2E real con Playwright queda pendiente para un C
 * futuro (`c-frontend-e2e-tests`); este test es el reemplazo mínimo
 * viable con React Testing Library que mantiene TDD estricto.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const { mockNotifState, setMockNotifState } = vi.hoisted(() => {
  const state = {
    unreadCount: 0,
    notificaciones: [] as Array<{
      id: string
      tipo: string
      mensaje: string
      leida: boolean
      fecha_lectura: string | null
      created_at: string
      entidad_tipo: string
      entidad_id: string
      empresa_id: string
    }>,
    loading: false,
    error: null as string | null,
    fetchNotificaciones: vi.fn(),
    marcarLeida: vi.fn(),
    marcarTodasLeidas: vi.fn(),
    clearError: vi.fn(),
  }
  return { mockNotifState: state, setMockNotifState: (next: Partial<typeof state>) => Object.assign(state, next) }
})

const { mockAuthState, setMockAuthState } = vi.hoisted(() => {
  const state = {
    user: { id: 'u-1', email: 'admin@test', nombre: 'Admin', apellido: 'L', rol: 'admin' },
    isAuthenticated: true,
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
  useNotificacionStore: (selector?: (s: typeof mockNotifState) => unknown) => {
    return selector ? selector(mockNotifState) : mockNotifState
  },
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  }
})

import { Header } from '@/components/layout/Header'

function renderHeader() {
  return render(
    <MemoryRouter>
      <Header onToggleSidebar={vi.fn()} />
    </MemoryRouter>,
  )
}

describe('Flujo de notificaciones (badge + panel)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setMockNotifState({
      unreadCount: 0,
      notificaciones: [],
      loading: false,
      error: null,
    })
    mockNotifState.marcarLeida.mockResolvedValue(undefined)
    mockNotifState.marcarTodasLeidas.mockResolvedValue(undefined)
    setMockAuthState({
      user: { id: 'u-1', email: 'admin@test', nombre: 'Admin', apellido: 'L', rol: 'admin' },
      isAuthenticated: true,
    })
  })

  it('badge muestra contador, panel aparece al click, marcar leída actualiza store', () => {
    setMockNotifState({
      unreadCount: 2,
      notificaciones: [
        {
          id: 'n1',
          tipo: 'stock_bajo',
          mensaje: 'Asado: 2 kg (mín 5 kg)',
          leida: false,
          fecha_lectura: null,
          created_at: new Date().toISOString(),
          entidad_tipo: 'producto',
          entidad_id: 'p1',
          empresa_id: 'e1',
        },
        {
          id: 'n2',
          tipo: 'diferencia_caja',
          mensaje: 'Diferencia de $500 en cierre',
          leida: false,
          fecha_lectura: null,
          created_at: new Date().toISOString(),
          entidad_tipo: 'caja',
          entidad_id: 'c1',
          empresa_id: 'e1',
        },
      ],
    })

    renderHeader()

    // Badge visible con contador
    expect(screen.getByTestId('notification-badge-count')).toHaveTextContent('2')

    // Panel oculto hasta el click
    expect(screen.queryByTestId('notification-panel')).not.toBeInTheDocument()

    // Click en el badge abre el panel
    fireEvent.click(screen.getByRole('button', { name: /notificaciones/i }))
    expect(screen.getByTestId('notification-panel')).toBeInTheDocument()

    // Las 2 notificaciones están listadas
    const list = screen.getByTestId('notification-list')
    expect(within(list).getByText('Asado: 2 kg (mín 5 kg)')).toBeInTheDocument()
    expect(within(list).getByText('Diferencia de $500 en cierre')).toBeInTheDocument()

    // Marcar como leída (hay un botón por no-leída; click en el de n1)
    const btn = screen.getByTestId('notification-mark-read-n1')
    fireEvent.click(btn)
    expect(mockNotifState.marcarLeida).toHaveBeenCalledWith('n1')
  })

  it('badge sin no leídas: contador oculto, panel sigue funcionando', () => {
    setMockNotifState({
      unreadCount: 0,
      notificaciones: [
        {
          id: 'n-old',
          tipo: 'stock_bajo',
          mensaje: 'Notificación leída',
          leida: true,
          fecha_lectura: '2026-06-20T10:00:00Z',
          created_at: '2026-06-19T10:00:00Z',
          entidad_tipo: 'producto',
          entidad_id: 'p1',
          empresa_id: 'e1',
        },
      ],
    })

    renderHeader()
    expect(screen.queryByTestId('notification-badge-count')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /notificaciones/i }))
    expect(screen.getByTestId('notification-panel')).toBeInTheDocument()
    expect(screen.getByText('Notificación leída')).toBeInTheDocument()
  })
})
