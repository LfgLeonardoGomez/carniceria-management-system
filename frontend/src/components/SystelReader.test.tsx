import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { SystelReader } from './SystelReader'

describe('SystelReader', () => {
  const onProductRead = vi.fn()
  const onError = vi.fn()

  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('debería renderizar un input oculto', () => {
    render(<SystelReader onProductRead={onProductRead} onError={onError} />)
    const input = screen.getByTestId('systel-reader-input')
    expect(input).toHaveAttribute('aria-hidden', 'true')
    expect(input).toHaveAttribute('tabIndex', '-1')
  })

  it('debería llamar onProductRead al recibir 13 dígitos válidos', () => {
    render(<SystelReader onProductRead={onProductRead} onError={onError} />)
    const input = screen.getByTestId('systel-reader-input') as HTMLInputElement

    act(() => {
      for (const digit of '2000270048052') {
        fireEvent.keyDown(input, { key: digit })
      }
    })

    expect(onProductRead).toHaveBeenCalledTimes(1)
    expect(onProductRead).toHaveBeenCalledWith({ plu: '00027', pesoKg: 4.805 })
  })

  it('debería ignorar caracteres no numéricos', () => {
    render(<SystelReader onProductRead={onProductRead} onError={onError} />)
    const input = screen.getByTestId('systel-reader-input') as HTMLInputElement

    act(() => {
      fireEvent.keyDown(input, { key: 'a' })
      fireEvent.keyDown(input, { key: '!' })
      for (const digit of '2000270048052') {
        fireEvent.keyDown(input, { key: digit })
      }
    })

    expect(onProductRead).toHaveBeenCalledTimes(1)
    expect(onProductRead).toHaveBeenCalledWith({ plu: '00027', pesoKg: 4.805 })
  })

  it('debería limpiar el buffer tras timeout de 100ms sin dígitos', () => {
    render(<SystelReader onProductRead={onProductRead} onError={onError} />)
    const input = screen.getByTestId('systel-reader-input') as HTMLInputElement

    act(() => {
      fireEvent.keyDown(input, { key: '2' })
      fireEvent.keyDown(input, { key: '0' })
      fireEvent.keyDown(input, { key: '0' })
    })

    // Avanzar 100ms → timeout limpia buffer
    act(() => {
      vi.advanceTimersByTime(100)
    })

    // Ahora enviar el resto del código
    act(() => {
      for (const digit of '0270048052') {
        fireEvent.keyDown(input, { key: digit })
      }
    })

    // Como se limpió el buffer, ahora tiene 10 dígitos, no 13
    expect(onProductRead).not.toHaveBeenCalled()

    // Avanzar otro timeout para limpiar
    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(onError).not.toHaveBeenCalled()
  })

  it('debería re-enfocar automáticamente al perder foco', async () => {
    render(<SystelReader onProductRead={onProductRead} onError={onError} />)
    const input = screen.getByTestId('systel-reader-input') as HTMLInputElement

    act(() => {
      input.focus()
    })
    expect(document.activeElement).toBe(input)

    act(() => {
      input.blur()
    })

    // Avanzar debounce de 50ms
    act(() => {
      vi.advanceTimersByTime(50)
    })

    await waitFor(() => {
      expect(document.activeElement).toBe(input)
    })
  })

  it('no debería llamar onProductRead si el código tiene prefijo inválido', () => {
    render(<SystelReader onProductRead={onProductRead} onError={onError} />)
    const input = screen.getByTestId('systel-reader-input') as HTMLInputElement

    act(() => {
      for (const digit of '1000270048052') {
        fireEvent.keyDown(input, { key: digit })
      }
    })

    expect(onProductRead).not.toHaveBeenCalled()
    expect(onError).toHaveBeenCalledTimes(1)
  })
})
