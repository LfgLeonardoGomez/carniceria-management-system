import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    user: { id: 'u-1', email: 'u@e.com', nombre: 'A', apellido: 'B', rol: 'admin' },
    isAuthenticated: true,
    setUser: vi.fn(),
    setToken: vi.fn(),
    setImpersonating: vi.fn(),
    logout: vi.fn(),
  }),
}))

function renderApp(initialPath: string = '/', children: ReactNode = <div data-testid="page-content">Hello</div>) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AppLayout>{children}</AppLayout>
    </MemoryRouter>,
  )
}

describe('AppLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders Sidebar, Header, and the main content area', () => {
    renderApp()
    expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    expect(screen.getByTestId('header')).toBeInTheDocument()
  })

  it('renders children inside <main>', () => {
    renderApp()
    const main = screen.getByRole('main')
    expect(main).toBeInTheDocument()
    expect(withinMain(main)).toHaveTextContent('Hello')
  })

  it('clicking the hamburger toggles the sidebar width', () => {
    renderApp()
    const sidebarBefore = screen.getByTestId('sidebar')
    expect(sidebarBefore.className).toMatch(/w-60/)

    const hamburger = screen.getByRole('button', { name: /toggle|menú lateral/i })
    fireEvent.click(hamburger)

    const sidebarAfter = screen.getByTestId('sidebar')
    expect(sidebarAfter.className).toMatch(/w-16/)
  })

  it('clicking the sidebar collapse button also toggles to collapsed', () => {
    renderApp()
    const sidebar = screen.getByTestId('sidebar')
    expect(sidebar.className).toMatch(/w-60/)

    const collapseBtn = screen.getByRole('button', { name: /colapsar sidebar/i })
    fireEvent.click(collapseBtn)

    expect(screen.getByTestId('sidebar').className).toMatch(/w-16/)
  })

  it('persists the collapsed state in localStorage', () => {
    renderApp()
    fireEvent.click(screen.getByRole('button', { name: /toggle|menú lateral/i }))
    expect(localStorage.getItem('basile.sidebar.collapsed')).toBe('true')
  })

  it('starts collapsed when localStorage flag is true', () => {
    localStorage.setItem('basile.sidebar.collapsed', 'true')
    renderApp()
    expect(screen.getByTestId('sidebar').className).toMatch(/w-16/)
  })

  it('starts expanded when localStorage flag is missing', () => {
    localStorage.removeItem('basile.sidebar.collapsed')
    renderApp()
    expect(screen.getByTestId('sidebar').className).toMatch(/w-60/)
  })

  it('starts expanded when localStorage flag is "false"', () => {
    localStorage.setItem('basile.sidebar.collapsed', 'false')
    renderApp()
    expect(screen.getByTestId('sidebar').className).toMatch(/w-60/)
  })
})

function withinMain(main: HTMLElement): HTMLElement {
  return main.querySelector('[data-testid="page-content"]') as HTMLElement
}
