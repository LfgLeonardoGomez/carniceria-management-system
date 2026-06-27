import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { NotificationPanel } from '@/components/notifications/NotificationPanel'

const { mockState, setMockState } = vi.hoisted(() => {
  const state = {
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
    marcarLeida: vi.fn(),
    marcarTodasLeidas: vi.fn(),
    clearError: vi.fn(),
  }
  return { mockState: state, setMockState: (next: Partial<typeof state>) => Object.assign(state, next) }
})

vi.mock('@/stores/notificacionStore', () => ({
  useNotificacionStore: (selector?: (s: typeof mockState) => unknown) => {
    return selector ? selector(mockState) : mockState
  },
}))

describe('NotificationPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setMockState({
      notificaciones: [],
      loading: false,
      error: null,
    })
    mockState.marcarLeida.mockResolvedValue(undefined)
    mockState.marcarTodasLeidas.mockResolvedValue(undefined)
  })

  it('muestra estado vacío cuando no hay notificaciones', () => {
    render(<NotificationPanel onClose={vi.fn()} />)
    expect(screen.getByText(/no tenés notificaciones/i)).toBeInTheDocument()
  })

  it('renderiza la lista de notificaciones', () => {
    setMockState({
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
          created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
          entidad_tipo: 'caja',
          entidad_id: 'c1',
          empresa_id: 'e1',
        },
      ],
    })

    render(<NotificationPanel onClose={vi.fn()} />)
    expect(screen.getByText('Asado: 2 kg (mín 5 kg)')).toBeInTheDocument()
    expect(screen.getByText('Diferencia de $500 en cierre')).toBeInTheDocument()
  })

  it('marca una notificación como leída al hacer click en el botón', async () => {
    setMockState({
      notificaciones: [
        {
          id: 'n1',
          tipo: 'stock_bajo',
          mensaje: 'Asado bajo',
          leida: false,
          fecha_lectura: null,
          created_at: new Date().toISOString(),
          entidad_tipo: 'producto',
          entidad_id: 'p1',
          empresa_id: 'e1',
        },
      ],
    })
    render(<NotificationPanel onClose={vi.fn()} />)
    const btn = screen.getByRole('button', { name: /marcar como leída/i })
    fireEvent.click(btn)
    expect(mockState.marcarLeida).toHaveBeenCalledWith('n1')
  })

  it('llama a marcarTodasLeidas al click en "Marcar todas"', () => {
    setMockState({
      notificaciones: [
        {
          id: 'n1',
          tipo: 'stock_bajo',
          mensaje: 'X',
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
          mensaje: 'Y',
          leida: false,
          fecha_lectura: null,
          created_at: new Date().toISOString(),
          entidad_tipo: 'caja',
          entidad_id: 'c1',
          empresa_id: 'e1',
        },
      ],
    })
    render(<NotificationPanel onClose={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: /marcar todas como leídas/i }))
    expect(mockState.marcarTodasLeidas).toHaveBeenCalledTimes(1)
  })

  it('muestra tiempo relativo formateado (hace X minutos)', () => {
    setMockState({
      notificaciones: [
        {
          id: 'n1',
          tipo: 'stock_bajo',
          mensaje: 'X',
          leida: false,
          fecha_lectura: null,
          created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
          entidad_tipo: 'producto',
          entidad_id: 'p1',
          empresa_id: 'e1',
        },
      ],
    })
    render(<NotificationPanel onClose={vi.fn()} />)
    expect(screen.getByText(/hace 5 min/i)).toBeInTheDocument()
  })

  it('muestra un error del store si lo hay', () => {
    setMockState({ error: 'Falló la conexión' })
    render(<NotificationPanel onClose={vi.fn()} />)
    expect(screen.getByText('Falló la conexión')).toBeInTheDocument()
  })

  it('llama a onClose al hacer click fuera del panel (mousedown en body)', () => {
    setMockState({})
    const onClose = vi.fn()
    render(<NotificationPanel onClose={onClose} />)
    fireEvent.mouseDown(document.body)
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
