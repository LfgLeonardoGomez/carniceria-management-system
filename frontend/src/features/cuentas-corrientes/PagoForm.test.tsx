/**
 * Tests for PagoForm (Task 6.1 RED → GREEN).
 *
 * TDD cycle:
 *   6.1 RED  — payment form validates positive amount; submits to payments endpoint;
 *              renders returned new balance
 *   TRIANGULATE — form shows error for 0/negative; surfacess 409 overpayment error
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PagoForm } from './PagoForm'

// Mock the API module
vi.mock('./api', () => ({
  registrarPago: vi.fn(),
}))

import { registrarPago } from './api'
const mockedRegistrarPago = vi.mocked(registrarPago)

const CLIENTE_ID = '11111111-1111-1111-1111-111111111111'

describe('PagoForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the importe input and submit button', () => {
    render(<PagoForm clienteId={CLIENTE_ID} onSuccess={vi.fn()} />)
    expect(screen.getByLabelText(/importe/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /registrar pago/i })).toBeInTheDocument()
  })

  it('submits the form with a valid positive amount', async () => {
    const user = userEvent.setup()
    const onSuccess = vi.fn()

    mockedRegistrarPago.mockResolvedValueOnce({
      movimiento: {
        id: 'mov-1',
        tipo: 'pago',
        importe: '300.00',
        saldo_resultante: '700.00',
        venta_id: null,
        fecha: '2026-06-23T12:00:00Z',
      },
      saldo_actual: '700.00',
    })

    render(<PagoForm clienteId={CLIENTE_ID} onSuccess={onSuccess} />)

    await user.clear(screen.getByLabelText(/importe/i))
    await user.type(screen.getByLabelText(/importe/i), '300.00')
    await user.click(screen.getByRole('button', { name: /registrar pago/i }))

    await waitFor(() => {
      expect(mockedRegistrarPago).toHaveBeenCalledWith(CLIENTE_ID, { importe: '300.00' })
    })
    expect(onSuccess).toHaveBeenCalledWith('700.00')
  })

  it('renders the new balance after successful payment', async () => {
    const user = userEvent.setup()

    mockedRegistrarPago.mockResolvedValueOnce({
      movimiento: {
        id: 'mov-2',
        tipo: 'pago',
        importe: '1000.00',
        saldo_resultante: '0.00',
        venta_id: null,
        fecha: '2026-06-23T12:00:00Z',
      },
      saldo_actual: '0.00',
    })

    render(<PagoForm clienteId={CLIENTE_ID} onSuccess={vi.fn()} />)

    await user.type(screen.getByLabelText(/importe/i), '1000.00')
    await user.click(screen.getByRole('button', { name: /registrar pago/i }))

    await waitFor(() => {
      expect(screen.getByTestId('pago-success-saldo')).toHaveTextContent('0.00')
    })
  })

  // TRIANGULATE — zero/negative importe should show client-side validation error
  it('shows validation error for zero importe', async () => {
    const user = userEvent.setup()
    render(<PagoForm clienteId={CLIENTE_ID} onSuccess={vi.fn()} />)

    await user.clear(screen.getByLabelText(/importe/i))
    await user.type(screen.getByLabelText(/importe/i), '0')
    await user.click(screen.getByRole('button', { name: /registrar pago/i }))

    await waitFor(() => {
      expect(screen.getByTestId('pago-error')).toBeInTheDocument()
    })
    expect(mockedRegistrarPago).not.toHaveBeenCalled()
  })

  it('shows validation error for negative importe', async () => {
    const user = userEvent.setup()
    render(<PagoForm clienteId={CLIENTE_ID} onSuccess={vi.fn()} />)

    await user.clear(screen.getByLabelText(/importe/i))
    await user.type(screen.getByLabelText(/importe/i), '-50')
    await user.click(screen.getByRole('button', { name: /registrar pago/i }))

    await waitFor(() => {
      expect(screen.getByTestId('pago-error')).toBeInTheDocument()
    })
    expect(mockedRegistrarPago).not.toHaveBeenCalled()
  })

  // TRIANGULATE — 409 overpayment error is surfaced
  it('surfaces 409 overpayment error to user', async () => {
    const user = userEvent.setup()

    const axiosError = {
      response: { status: 409, data: { detail: 'El importe supera el saldo actual.' } },
    }
    mockedRegistrarPago.mockRejectedValueOnce(axiosError)

    render(<PagoForm clienteId={CLIENTE_ID} onSuccess={vi.fn()} />)

    await user.type(screen.getByLabelText(/importe/i), '9999.00')
    await user.click(screen.getByRole('button', { name: /registrar pago/i }))

    await waitFor(() => {
      expect(screen.getByTestId('pago-error')).toBeInTheDocument()
    })
    expect(screen.getByTestId('pago-error').textContent).toMatch(/supera|excede|pago/i)
  })
})
