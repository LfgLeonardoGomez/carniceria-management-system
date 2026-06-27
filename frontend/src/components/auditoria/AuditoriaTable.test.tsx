import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { AuditoriaTable } from '@/components/auditoria/AuditoriaTable'

const { mockRegistros, setMockRegistros } = vi.hoisted(() => {
  const registros: Array<{
    id: string
    empresa_id: string
    usuario_id: string | null
    accion: string
    entidad_tipo: string
    entidad_id: string | null
    payload: Record<string, unknown> | null
    fecha: string
    hora: string
    created_at: string
  }> = []
  return { mockRegistros: registros, setMockRegistros: (next: typeof registros) => {
    mockRegistros.length = 0
    mockRegistros.push(...next)
  } }
})

vi.mock('@/stores/auditoriaStore', () => ({
  useAuditoriaStore: (selector?: (s: { registros: typeof mockRegistros }) => unknown) => {
    const state = { registros: mockRegistros }
    return selector ? selector(state) : state
  },
}))

describe('AuditoriaTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setMockRegistros([])
  })

  it('muestra estado vacío cuando no hay registros', () => {
    render(<AuditoriaTable />)
    expect(screen.getByText(/no hay registros de auditoría/i)).toBeInTheDocument()
  })

  it('renderiza una fila por cada registro con columnas visibles', () => {
    setMockRegistros([
      {
        id: 'r1',
        empresa_id: 'e1',
        usuario_id: 'u1',
        accion: 'CREAR',
        entidad_tipo: 'cliente',
        entidad_id: 'cli1',
        payload: { nombre: 'Juan' },
        fecha: '2026-06-25',
        hora: '14:30:00',
        created_at: '2026-06-25T14:30:00Z',
      },
    ])
    render(<AuditoriaTable />)
    const fila = screen.getByTestId('auditoria-row-r1')
    expect(within(fila).getByText('CREAR')).toBeInTheDocument()
    expect(within(fila).getByText('cliente')).toBeInTheDocument()
    expect(within(fila).getByText('cli1')).toBeInTheDocument()
  })

  it('muestra el payload como JSON dentro de <details>', () => {
    setMockRegistros([
      {
        id: 'r1',
        empresa_id: 'e1',
        usuario_id: null,
        accion: 'CREAR',
        entidad_tipo: 'venta',
        entidad_id: 'v1',
        payload: { total: 1500 },
        fecha: '2026-06-25',
        hora: '10:00:00',
        created_at: '2026-06-25T10:00:00Z',
      },
    ])
    render(<AuditoriaTable />)
    const details = screen.getByTestId('auditoria-payload-r1')
    expect(details.tagName.toLowerCase()).toBe('details')
    expect(details.textContent).toContain('1500')
  })

  it('renderiza el ID de usuario cuando no se provee nombre', () => {
    setMockRegistros([
      {
        id: 'r1',
        empresa_id: 'e1',
        usuario_id: 'usuario-99',
        accion: 'CREAR',
        entidad_tipo: 'cliente',
        entidad_id: 'cli1',
        payload: null,
        fecha: '2026-06-25',
        hora: '10:00:00',
        created_at: '2026-06-25T10:00:00Z',
      },
    ])
    render(<AuditoriaTable usuarioNombrePorId={() => null} />)
    const fila = screen.getByTestId('auditoria-row-r1')
    expect(within(fila).getByText('usuario-99')).toBeInTheDocument()
  })

  it('renderiza el nombre resuelto cuando usuarioNombrePorId devuelve', () => {
    setMockRegistros([
      {
        id: 'r1',
        empresa_id: 'e1',
        usuario_id: 'u1',
        accion: 'CREAR',
        entidad_tipo: 'cliente',
        entidad_id: 'cli1',
        payload: null,
        fecha: '2026-06-25',
        hora: '10:00:00',
        created_at: '2026-06-25T10:00:00Z',
      },
    ])
    render(<AuditoriaTable usuarioNombrePorId={(id) => (id === 'u1' ? 'Carlos López' : null)} />)
    expect(screen.getByText('Carlos López')).toBeInTheDocument()
  })

  it('muestra "sistema" cuando usuario_id es null', () => {
    setMockRegistros([
      {
        id: 'r1',
        empresa_id: 'e1',
        usuario_id: null,
        accion: 'CREAR',
        entidad_tipo: 'cliente',
        entidad_id: 'cli1',
        payload: null,
        fecha: '2026-06-25',
        hora: '10:00:00',
        created_at: '2026-06-25T10:00:00Z',
      },
    ])
    render(<AuditoriaTable />)
    expect(screen.getByText('sistema')).toBeInTheDocument()
  })
})
