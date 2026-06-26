import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Header } from '@/components/layout/Header'

const { mockAuthStoreState, currentUser } = vi.hoisted(() => {
  const state = {
    user: {
      id: 'u-1',
      email: 'carlos@example.com',
      nombre: 'Carlos',
      apellido: 'López',
      rol: 'admin',
    } as { id: string; email: string; nombre: string; apellido: string; rol: string } | null,
  }
  const stableState = {
    user: state.user,
    isAuthenticated: true,
    setUser: vi.fn(),
    setToken: vi.fn(),
    setImpersonating: vi.fn(),
    logout: vi.fn(),
  }
  return { mockAuthStoreState: () => stableState, currentUser: state }
})

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector?: (s: ReturnType<typeof mockAuthStoreState>) => unknown) => {
    const state = mockAuthStoreState()
    return selector ? selector(state) : state
  },
}))

vi.mock('@/stores/notificacionStore', () => ({
  useNotificacionStore: (selector?: (s: { unreadCount: number }) => unknown) => {
    const state = { unreadCount: 0 }
    return selector ? selector(state) : state
  },
}))

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

function renderHeader() {
  return render(
    <MemoryRouter>
      <Header onToggleSidebar={vi.fn()} />
    </MemoryRouter>,
  )
}

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    currentUser.user = {
      id: 'u-1',
      email: 'carlos@example.com',
      nombre: 'Carlos',
      apellido: 'López',
      rol: 'admin',
    }
  })

  it('renders the user full name in the dropdown trigger', () => {
    renderHeader()
    expect(screen.getByText('Carlos López')).toBeInTheDocument()
  })

  it('does not render the dropdown menu until the trigger is clicked', () => {
    renderHeader()
    expect(screen.queryByText('Mi perfil')).not.toBeInTheDocument()
    expect(screen.queryByText('Cerrar sesión')).not.toBeInTheDocument()
  })

  it('opens the dropdown when trigger is clicked', () => {
    renderHeader()
    fireEvent.click(screen.getByText('Carlos López'))
    expect(screen.getByText('Mi perfil')).toBeInTheDocument()
    expect(screen.getByText('Cerrar sesión')).toBeInTheDocument()
  })

  it('clicking "Mi perfil" navigates to /perfil and does NOT call logout', () => {
    renderHeader()
    fireEvent.click(screen.getByText('Carlos López'))
    fireEvent.click(screen.getByText('Mi perfil'))
    expect(mockNavigate).toHaveBeenCalledWith('/perfil')
    expect(mockAuthStoreState().logout).not.toHaveBeenCalled()
  })

  it('clicking "Cerrar sesión" calls logout, clears access_token, and navigates to /login', async () => {
    localStorage.setItem('access_token', 'fake-token')
    renderHeader()
    fireEvent.click(screen.getByText('Carlos López'))
    fireEvent.click(screen.getByText('Cerrar sesión'))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login')
    })
    expect(mockAuthStoreState().logout).toHaveBeenCalledTimes(1)
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('click-outside closes the dropdown', () => {
    renderHeader()
    fireEvent.click(screen.getByText('Carlos López'))
    expect(screen.getByText('Mi perfil')).toBeInTheDocument()

    fireEvent.mouseDown(document.body)
    expect(screen.queryByText('Mi perfil')).not.toBeInTheDocument()
  })

  it('renders the BASILE brand name (fallback while empresa context is not wired)', () => {
    renderHeader()
    expect(screen.getByText('BASILE')).toBeInTheDocument()
  })

  it('renders the hamburger button to toggle sidebar', () => {
    const onToggle = vi.fn()
    render(
      <MemoryRouter>
        <Header onToggleSidebar={onToggle} />
      </MemoryRouter>,
    )
    const hamburger = screen.getByRole('button', { name: /toggle|menú|hamburger/i })
    fireEvent.click(hamburger)
    expect(onToggle).toHaveBeenCalledTimes(1)
  })

  it('renders the user avatar with initials when name has 2 parts', () => {
    renderHeader()
    expect(screen.getByText('CL')).toBeInTheDocument()
  })
})
