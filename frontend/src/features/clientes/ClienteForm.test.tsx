import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ClienteForm } from '@/features/clientes/ClienteForm'
import type { Cliente } from '@/shared/types/cliente'

const mockCliente: Cliente = {
  id: 'c1',
  empresa_id: 'emp-1',
  nombre: 'Carlos',
  apellido: 'Gómez',
  razon_social: 'Gómez Hnos',
  cuit: '20123456786',
  telefono: '123456789',
  email: 'carlos@test.com',
  direccion: 'Calle 123',
  tipo_cliente: 'mayorista',
  limite_cuenta_corriente: '5000.0000',
  saldo_actual: '1500.0000',
  activo: true,
  created_at: '',
  updated_at: '',
}

describe('ClienteForm', () => {
  it('renders create form', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ClienteForm cliente={null} onSubmit={onSubmit} onCancel={onCancel} loading={false} />)

    expect(screen.getByText('Nuevo Cliente')).toBeInTheDocument()
    expect(screen.getByLabelText(/Nombre/i)).toBeInTheDocument()
  })

  it('renders edit form with cliente data', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ClienteForm cliente={mockCliente} onSubmit={onSubmit} onCancel={onCancel} loading={false} />)

    expect(screen.getByText('Editar Cliente')).toBeInTheDocument()
    const nombreInput = screen.getByLabelText(/Nombre/i) as HTMLInputElement
    expect(nombreInput.value).toBe('Carlos')
  })

  it('submits valid data', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ClienteForm cliente={null} onSubmit={onSubmit} onCancel={onCancel} loading={false} />)

    fireEvent.change(screen.getByLabelText(/Nombre/i), { target: { value: 'Juan' } })
    fireEvent.change(screen.getByLabelText(/Apellido/i), { target: { value: 'Pérez' } })
    fireEvent.change(screen.getByLabelText(/CUIT/i), { target: { value: '20123456786' } })

    fireEvent.click(screen.getByText('Crear'))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          nombre: 'Juan',
          apellido: 'Pérez',
          cuit: '20123456786',
        })
      )
    })
  })

  it('rejects invalid CUIT', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ClienteForm cliente={null} onSubmit={onSubmit} onCancel={onCancel} loading={false} />)

    fireEvent.change(screen.getByLabelText(/Nombre/i), { target: { value: 'Juan' } })
    fireEvent.change(screen.getByLabelText(/CUIT/i), { target: { value: '123' } })

    fireEvent.click(screen.getByText('Crear'))

    await waitFor(() => {
      expect(screen.getByText('CUIT inválido (debe tener 11 dígitos)')).toBeInTheDocument()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('rejects empty nombre', async () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ClienteForm cliente={null} onSubmit={onSubmit} onCancel={onCancel} loading={false} />)

    fireEvent.click(screen.getByText('Crear'))

    await waitFor(() => {
      expect(screen.getByText('El nombre es obligatorio')).toBeInTheDocument()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('calls onCancel when cancel button clicked', () => {
    const onSubmit = vi.fn()
    const onCancel = vi.fn()

    render(<ClienteForm cliente={null} onSubmit={onSubmit} onCancel={onCancel} loading={false} />)

    fireEvent.click(screen.getByText('Cancelar'))
    expect(onCancel).toHaveBeenCalled()
  })
})
