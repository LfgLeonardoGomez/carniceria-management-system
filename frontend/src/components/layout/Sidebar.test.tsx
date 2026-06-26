import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Sidebar } from '@/components/layout/Sidebar'

const { mockAuthStoreState, currentRol } = vi.hoisted(() => {
  const state = { currentRol: 'admin' as string | null }
  const factory = (rol: string | null) => ({
    user: rol
      ? { id: 'u-1', email: 'u@e.com', nombre: 'User', apellido: 'Test', rol }
      : null,
    isAuthenticated: !!rol,
    setUser: vi.fn(),
    setToken: vi.fn(),
    setImpersonating: vi.fn(),
    logout: vi.fn(),
  })
  return { mockAuthStoreState: factory, currentRol: state }
})

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector?: (s: ReturnType<typeof mockAuthStoreState>) => unknown) => {
    const state = mockAuthStoreState(currentRol.currentRol)
    return selector ? selector(state) : state
  },
}))

function renderSidebar(initialPath: string = '/', collapsed = false) {
  const onToggle = vi.fn()
  const utils = render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Sidebar collapsed={collapsed} onToggle={onToggle} />
    </MemoryRouter>,
  )
  return { ...utils, onToggle }
}

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    currentRol.currentRol = 'admin'
  })

  it('admin sees every menu item declared in menuConfig', () => {
    currentRol.currentRol = 'admin'
    renderSidebar()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Venta')).toBeInTheDocument()
    expect(screen.getByText('Productos')).toBeInTheDocument()
    expect(screen.getByText('Stock')).toBeInTheDocument()
    expect(screen.getByText('Compras')).toBeInTheDocument()
    expect(screen.getByText('Despostes')).toBeInTheDocument()
    expect(screen.getByText('Clientes')).toBeInTheDocument()
    expect(screen.getByText('Proveedores')).toBeInTheDocument()
    expect(screen.getByText('Cuentas Corrientes')).toBeInTheDocument()
    expect(screen.getByText('Caja')).toBeInTheDocument()
    expect(screen.getByText('Gastos')).toBeInTheDocument()
    expect(screen.getByText('Reportes')).toBeInTheDocument()
    expect(screen.getByText('Reportes Financieros')).toBeInTheDocument()
    expect(screen.getByText('Rentabilidad')).toBeInTheDocument()
    expect(screen.getByText('Usuarios')).toBeInTheDocument()
    expect(screen.getByText('Configuración Empresa')).toBeInTheDocument()
    expect(screen.getByText('Perfil')).toBeInTheDocument()
  })

  it('cajero does NOT see admin-only items (Usuarios, Reportes Financieros, Rentabilidad, Configuración Empresa)', () => {
    currentRol.currentRol = 'cajero'
    renderSidebar()
    expect(screen.queryByText('Usuarios')).not.toBeInTheDocument()
    expect(screen.queryByText('Reportes Financieros')).not.toBeInTheDocument()
    expect(screen.queryByText('Rentabilidad')).not.toBeInTheDocument()
    expect(screen.queryByText('Configuración Empresa')).not.toBeInTheDocument()
  })

  it('cajero DOES see allowed items', () => {
    currentRol.currentRol = 'cajero'
    renderSidebar()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Venta')).toBeInTheDocument()
    expect(screen.getByText('Clientes')).toBeInTheDocument()
    expect(screen.getByText('Cuentas Corrientes')).toBeInTheDocument()
    expect(screen.getByText('Caja')).toBeInTheDocument()
    expect(screen.getByText('Perfil')).toBeInTheDocument()
  })

  it('vendedor sees only Dashboard, Venta, Perfil', () => {
    currentRol.currentRol = 'vendedor'
    renderSidebar()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Venta')).toBeInTheDocument()
    expect(screen.getByText('Perfil')).toBeInTheDocument()
    expect(screen.queryByText('Clientes')).not.toBeInTheDocument()
    expect(screen.queryByText('Caja')).not.toBeInTheDocument()
    expect(screen.queryByText('Productos')).not.toBeInTheDocument()
  })

  it('encargado does NOT see admin-only (Usuarios, Configuración Empresa)', () => {
    currentRol.currentRol = 'encargado'
    renderSidebar()
    expect(screen.queryByText('Usuarios')).not.toBeInTheDocument()
    expect(screen.queryByText('Configuración Empresa')).not.toBeInTheDocument()
    expect(screen.getByText('Productos')).toBeInTheDocument()
    expect(screen.getByText('Caja')).toBeInTheDocument()
  })

  it('superadmin sees admin-only items', () => {
    currentRol.currentRol = 'superadmin'
    renderSidebar()
    expect(screen.getByText('Usuarios')).toBeInTheDocument()
    expect(screen.getByText('Configuración Empresa')).toBeInTheDocument()
  })

  it('click on toggle calls onToggle', () => {
    const { onToggle } = renderSidebar('/', false)
    const toggleBtn = screen.getByRole('button', { name: /colapsar|expandir|chevron/i })
    fireEvent.click(toggleBtn)
    expect(onToggle).toHaveBeenCalledTimes(1)
  })

  it('renders expanded width by default and collapsed width when collapsed=true', () => {
    const { rerender } = render(
      <MemoryRouter>
        <Sidebar collapsed={false} onToggle={vi.fn()} />
      </MemoryRouter>,
    )
    const aside = screen.getByRole('complementary')
    expect(aside.className).toMatch(/w-60/)

    rerender(
      <MemoryRouter>
        <Sidebar collapsed={true} onToggle={vi.fn()} />
      </MemoryRouter>,
    )
    const asideCollapsed = screen.getByRole('complementary')
    expect(asideCollapsed.className).toMatch(/w-16/)
  })

  it('active NavLink has bg-primary-50 class', () => {
    currentRol.currentRol = 'admin'
    renderSidebar('/productos')
    const productosLink = screen.getByRole('link', { name: /productos/i })
    expect(productosLink.className).toMatch(/bg-primary-50/)
  })

  it('non-active NavLink does NOT have bg-primary-50 class', () => {
    currentRol.currentRol = 'admin'
    renderSidebar('/productos')
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i })
    expect(dashboardLink.className).not.toMatch(/bg-primary-50/)
  })

  it('renders section headers (Operaciones, Catálogo, Gestión, Administración)', () => {
    currentRol.currentRol = 'admin'
    renderSidebar()
    expect(screen.getByText('Operaciones')).toBeInTheDocument()
    expect(screen.getByText('Catálogo')).toBeInTheDocument()
    expect(screen.getByText('Gestión')).toBeInTheDocument()
    expect(screen.getByText('Administración')).toBeInTheDocument()
  })

  it('when collapsed, item labels are visually hidden but link still navigable', () => {
    currentRol.currentRol = 'admin'
    renderSidebar('/', true)
    const posLink = screen.getByRole('link', { name: 'Venta' })
    expect(posLink).toBeInTheDocument()
    expect(posLink.className).toMatch(/justify-center/)
  })
})
