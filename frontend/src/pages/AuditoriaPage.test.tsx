import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuditoriaPage } from '@/pages/AuditoriaPage'

const { mockState, setMockState } = vi.hoisted(() => {
  const state = {
    registros: [] as Array<{
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
    }>,
    total: 0,
    loading: false,
    error: null as string | null,
    filters: { skip: 0, limit: 50 } as Record<string, unknown>,
    fetchAuditoria: vi.fn(),
    setFilters: vi.fn(),
    exportarCSV: vi.fn(() => new Blob(['csv'], { type: 'text/csv' })),
    exportarJSON: vi.fn(() => new Blob(['json'], { type: 'application/json' })),
    clearError: vi.fn(),
  }
  return { mockState: state, setMockState: (next: Partial<typeof state>) => Object.assign(state, next) }
})

vi.mock('@/stores/auditoriaStore', () => ({
  useAuditoriaStore: (selector?: (s: typeof mockState) => unknown) => {
    return selector ? selector(mockState) : mockState
  },
}))

vi.mock('@/components/auditoria/AuditoriaTable', () => ({
  AuditoriaTable: () => <div data-testid="auditoria-table-mock">table</div>,
}))

function renderPage() {
  return render(
    <MemoryRouter>
      <AuditoriaPage />
    </MemoryRouter>,
  )
}

describe('AuditoriaPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setMockState({
      registros: [],
      total: 0,
      loading: false,
      error: null,
      filters: { skip: 0, limit: 50 },
    })
    mockState.fetchAuditoria.mockResolvedValue(undefined)
    mockState.setFilters.mockImplementation(() => undefined)
  })

  it('llama a fetchAuditoria al montar', () => {
    renderPage()
    expect(mockState.fetchAuditoria).toHaveBeenCalledTimes(1)
  })

  it('muestra el total de registros', () => {
    setMockState({ total: 42 })
    renderPage()
    expect(screen.getByText(/42 registros/i)).toBeInTheDocument()
  })

  it('aplica filtro de fecha_desde al cambiar el input', () => {
    renderPage()
    const input = screen.getByLabelText(/fecha desde/i)
    fireEvent.change(input, { target: { value: '2026-06-01' } })
    fireEvent.submit(input.closest('form')!)
    expect(mockState.setFilters).toHaveBeenCalledWith(
      expect.objectContaining({ fecha_desde: '2026-06-01' }),
    )
  })

  it('aplica filtro de accion al cambiar el select y submitir', () => {
    renderPage()
    const select = screen.getByLabelText(/acción/i)
    fireEvent.change(select, { target: { value: 'CREAR' } })
    fireEvent.submit(screen.getByTestId('auditoria-filters'))
    expect(mockState.setFilters).toHaveBeenCalledWith(
      expect.objectContaining({ accion: 'CREAR' }),
    )
  })

  it('dispara exportacion CSV', () => {
    setMockState({ registros: [{ id: 'r1' } as never] })
    // Mock createObjectURL + click en anchor
    const createObjectURLMock = vi.fn(() => 'blob:url')
    const revokeObjectURLMock = vi.fn()
    ;(URL as unknown as { createObjectURL: typeof createObjectURLMock }).createObjectURL = createObjectURLMock
    ;(URL as unknown as { revokeObjectURL: typeof revokeObjectURLMock }).revokeObjectURL = revokeObjectURLMock
    const clickMock = vi.fn()
    const origCreateElement = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation(((tag: string) => {
      const el = origCreateElement(tag) as HTMLElement
      if (tag === 'a') {
        (el as HTMLAnchorElement).click = clickMock
      }
      return el
    }) as typeof document.createElement)

    renderPage()
    const btn = screen.getByRole('button', { name: /exportar csv/i })
    fireEvent.click(btn)
    expect(mockState.exportarCSV).toHaveBeenCalledTimes(1)
    expect(createObjectURLMock).toHaveBeenCalled()
    expect(clickMock).toHaveBeenCalled()
  })

  it('dispara exportacion JSON', () => {
    setMockState({ registros: [{ id: 'r1' } as never] })
    const createObjectURLMock = vi.fn(() => 'blob:url')
    ;(URL as unknown as { createObjectURL: typeof createObjectURLMock }).createObjectURL = createObjectURLMock
    const clickMock = vi.fn()
    const origCreateElement = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation(((tag: string) => {
      const el = origCreateElement(tag) as HTMLElement
      if (tag === 'a') {
        (el as HTMLAnchorElement).click = clickMock
      }
      return el
    }) as typeof document.createElement)

    renderPage()
    const btn = screen.getByRole('button', { name: /exportar json/i })
    fireEvent.click(btn)
    expect(mockState.exportarJSON).toHaveBeenCalledTimes(1)
  })

  it('muestra error del store', () => {
    setMockState({ error: 'Sin permisos' })
    renderPage()
    expect(screen.getByText('Sin permisos')).toBeInTheDocument()
  })
})
