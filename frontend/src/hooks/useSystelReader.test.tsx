import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { useSystelReader } from './useSystelReader.tsx'
import { useCartStore } from '@/stores/cartStore'
import { buscarProductoPorPlu } from '@/shared/services/systelService'
import axios, { type AxiosError } from 'axios'

vi.mock('@/shared/services/systelService')
const mockedBuscarProductoPorPlu = vi.mocked(buscarProductoPorPlu)

function TestComponent({ enabled = true, onError }: { enabled?: boolean; onError?: (msg: string) => void }) {
  const { SystelReaderComponent } = useSystelReader({ enabled, onError })
  return <div>{SystelReaderComponent}</div>
}

describe('useSystelReader', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    useCartStore.setState({ items: [] })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('debería agregar producto al carrito cuando el backend responde exitosamente', async () => {
    mockedBuscarProductoPorPlu.mockResolvedValue({
      id: 'prod-1',
      empresa_id: 'emp-1',
      plu: '00027',
      nombre: 'Bife de Chorizo',
      categoria_id: null,
      precio_publico: '2499.99',
      precio_mayorista: '1999.99',
      costo_por_kilo: '1500.00',
      margen: '0.30',
      stock_actual: '100.000',
      stock_minimo: null,
      activo: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })

    render(<TestComponent enabled={true} />)

    act(() => {
      for (const digit of '2000270048052') {
        const input = screen.getByTestId('systel-reader-input') as HTMLInputElement
        input.dispatchEvent(new KeyboardEvent('keydown', { key: digit, bubbles: true }))
      }
    })

    await waitFor(() => {
      const items = useCartStore.getState().items
      expect(items).toHaveLength(1)
      expect(items[0].producto.plu).toBe('00027')
      expect(items[0].cantidadKg).toBe(4.805)
    })
  })

  it('debería manejar PLU no encontrado (404) sin agregar al carrito', async () => {
    const axiosError = new Error('Request failed') as Error & { response?: { status: number } }
    axiosError.response = { status: 404 }
    axios.isAxiosError = vi.fn((err: unknown): err is AxiosError => err === axiosError) as unknown as typeof axios.isAxiosError

    mockedBuscarProductoPorPlu.mockRejectedValue(axiosError)

    const onError = vi.fn()
    render(<TestComponent enabled={true} onError={onError} />)

    act(() => {
      for (const digit of '2999999999995') {
        const input = screen.getByTestId('systel-reader-input') as HTMLInputElement
        input.dispatchEvent(new KeyboardEvent('keydown', { key: digit, bubbles: true }))
      }
    })

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith('Producto no encontrado para el código escaneado')
      expect(useCartStore.getState().items).toHaveLength(0)
    })
  })

  it('debería manejar error de red sin agregar al carrito', async () => {
    const networkError = new Error('Network Error')
    axios.isAxiosError = vi.fn((err: unknown): err is AxiosError => err === networkError) as unknown as typeof axios.isAxiosError

    mockedBuscarProductoPorPlu.mockRejectedValue(networkError)

    const onError = vi.fn()
    render(<TestComponent enabled={true} onError={onError} />)

    act(() => {
      for (const digit of '2000270048052') {
        const input = screen.getByTestId('systel-reader-input') as HTMLInputElement
        input.dispatchEvent(new KeyboardEvent('keydown', { key: digit, bubbles: true }))
      }
    })

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith('Error de conexión al buscar el producto')
      expect(useCartStore.getState().items).toHaveLength(0)
    })
  })

  it('no debería duplicar ítems en lecturas rápidas', async () => {
    mockedBuscarProductoPorPlu.mockResolvedValue({
      id: 'prod-1',
      empresa_id: 'emp-1',
      plu: '00027',
      nombre: 'Bife de Chorizo',
      categoria_id: null,
      precio_publico: '2499.99',
      precio_mayorista: '1999.99',
      costo_por_kilo: '1500.00',
      margen: '0.30',
      stock_actual: '100.000',
      stock_minimo: null,
      activo: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })

    render(<TestComponent enabled={true} />)

    // Primera lectura
    act(() => {
      for (const digit of '2000270048052') {
        const input = screen.getByTestId('systel-reader-input') as HTMLInputElement
        input.dispatchEvent(new KeyboardEvent('keydown', { key: digit, bubbles: true }))
      }
    })

    // Segunda lectura inmediata
    act(() => {
      for (const digit of '2000270048052') {
        const input = screen.getByTestId('systel-reader-input') as HTMLInputElement
        input.dispatchEvent(new KeyboardEvent('keydown', { key: digit, bubbles: true }))
      }
    })

    await waitFor(() => {
      const items = useCartStore.getState().items
      expect(items).toHaveLength(1)
    })
  })
})
