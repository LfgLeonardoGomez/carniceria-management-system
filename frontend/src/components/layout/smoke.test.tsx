import { describe, it, expect, vi } from 'vitest'
import type { ReactNode } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    user: { id: 'u-1', email: 'admin@e.com', nombre: 'Admin', apellido: 'User', rol: 'admin' },
    isAuthenticated: true,
    setUser: vi.fn(),
    setToken: vi.fn(),
    setImpersonating: vi.fn(),
    logout: vi.fn(),
  }),
}))

import { AppLayout } from '@/components/layout/AppLayout'
import { LoginLayout } from '@/components/layout/LoginLayout'

function MockDashboard() {
  return <div>DashboardPageMock</div>
}
function MockProductos() {
  return <div>ProductosPageMock</div>
}
function MockLogin() {
  return <div>LoginPageMock</div>
}

function PrivateShell({ children }: { children: ReactNode }) {
  return <AppLayout>{children}</AppLayout>
}

describe('Smoke: routing + layout integration', () => {
  it('admin on / sees Dashboard inside AppLayout (sidebar + header + main)', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<PrivateShell><MockDashboard /></PrivateShell>} />
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    expect(screen.getByTestId('header')).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByText('DashboardPageMock')).toBeInTheDocument()
  })

  it('admin on /productos sees Productos inside AppLayout', () => {
    render(
      <MemoryRouter initialEntries={['/productos']}>
        <Routes>
          <Route path="/productos" element={<PrivateShell><MockProductos /></PrivateShell>} />
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    expect(screen.getByTestId('header')).toBeInTheDocument()
    expect(screen.getByText('ProductosPageMock')).toBeInTheDocument()
  })

  it('public /login renders LoginLayout (no sidebar/header, has BASILE brand)', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginLayout><MockLogin /></LoginLayout>} />
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument()
    expect(screen.queryByTestId('header')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'BASILE' })).toBeInTheDocument()
    expect(screen.getByText('LoginPageMock')).toBeInTheDocument()
  })

  it('sidebar persists collapsed state across remounts (localStorage)', () => {
    localStorage.setItem('basile.sidebar.collapsed', 'true')
    const { unmount } = render(
      <MemoryRouter>
        <PrivateShell><MockDashboard /></PrivateShell>
      </MemoryRouter>,
    )
    expect(screen.getByTestId('sidebar').className).toMatch(/w-16/)
    unmount()
    render(
      <MemoryRouter>
        <PrivateShell><MockDashboard /></PrivateShell>
      </MemoryRouter>,
    )
    expect(screen.getByTestId('sidebar').className).toMatch(/w-16/)
    localStorage.removeItem('basile.sidebar.collapsed')
  })

  it('hamburger toggle in header reflects in sidebar collapse', () => {
    render(
      <MemoryRouter>
        <PrivateShell><MockDashboard /></PrivateShell>
      </MemoryRouter>,
    )
    expect(screen.getByTestId('sidebar').className).toMatch(/w-60/)
    const hamburger = screen.getByRole('button', { name: /toggle|menú lateral/i })
    fireEvent.click(hamburger)
    expect(screen.getByTestId('sidebar').className).toMatch(/w-16/)
  })
})
