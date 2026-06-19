import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProveedorForm } from '@/features/proveedores/ProveedorForm'
import type { Proveedor } from '@/shared/types/proveedor'

describe('ProveedorForm', () => {
  it('renders create form', () => {
    render(
      <ProveedorForm
        proveedor={null}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
        loading={false}
        error={null}
      />,
    )
    expect(screen.getByText('Nuevo Proveedor')).toBeInTheDocument()
    expect(screen.getByLabelText(/Nombre/)).toBeInTheDocument()
    expect(screen.getByLabelText(/CUIT/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Teléfono/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Dirección/)).toBeInTheDocument()
  })

  it('renders edit form with values', () => {
    const proveedor: Proveedor = {
      id: '1',
      empresa_id: 'e1',
      nombre: 'Carnes del Sur',
      cuit: '30616874582',
      telefono: '123456789',
      email: 'contacto@carne.com',
      direccion: 'Av Siempre Viva 123',
      activo: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }
    render(
      <ProveedorForm
        proveedor={proveedor}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
        loading={false}
        error={null}
      />,
    )
    expect(screen.getByText('Editar Proveedor')).toBeInTheDocument()
    const nombreInput = screen.getByLabelText(/Nombre/) as HTMLInputElement
    expect(nombreInput.value).toBe('Carnes del Sur')
    const cuitInput = screen.getByLabelText(/CUIT/) as HTMLInputElement
    expect(cuitInput.value).toBe('30616874582')
  })

  it('validates nombre is required', () => {
    const onSubmit = vi.fn()
    render(
      <ProveedorForm
        proveedor={null}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
        loading={false}
        error={null}
      />,
    )
    fireEvent.submit(screen.getByText('Crear').closest('form')!)
    expect(screen.getByText('El nombre es obligatorio')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('validates CUIT format', () => {
    const onSubmit = vi.fn()
    render(
      <ProveedorForm
        proveedor={null}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
        loading={false}
        error={null}
      />,
    )
    const nombreInput = screen.getByLabelText(/Nombre/)
    fireEvent.change(nombreInput, { target: { value: 'Test' } })
    const cuitInput = screen.getByLabelText(/CUIT/)
    fireEvent.change(cuitInput, { target: { value: '123' } })
    fireEvent.submit(screen.getByText('Crear').closest('form')!)
    expect(screen.getByText('CUIT inválido (debe tener 11 dígitos)')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('validates email format', () => {
    const onSubmit = vi.fn()
    render(
      <ProveedorForm
        proveedor={null}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
        loading={false}
        error={null}
      />,
    )
    const nombreInput = screen.getByLabelText(/Nombre/)
    fireEvent.change(nombreInput, { target: { value: 'Test' } })
    const emailInput = screen.getByLabelText(/Email/)
    fireEvent.change(emailInput, { target: { value: 'no-es-email' } })
    fireEvent.submit(screen.getByText('Crear').closest('form')!)
    expect(screen.getByText('Email inválido')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('calls onSubmit with valid data', () => {
    const onSubmit = vi.fn()
    render(
      <ProveedorForm
        proveedor={null}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
        loading={false}
        error={null}
      />,
    )
    fireEvent.change(screen.getByLabelText(/Nombre/), { target: { value: 'Nuevo Proveedor' } })
    fireEvent.change(screen.getByLabelText(/CUIT/), { target: { value: '30616874582' } })
    fireEvent.change(screen.getByLabelText(/Teléfono/), { target: { value: '123456789' } })
    fireEvent.change(screen.getByLabelText(/Email/), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/Dirección/), { target: { value: 'Calle 123' } })
    fireEvent.submit(screen.getByText('Crear').closest('form')!)
    expect(onSubmit).toHaveBeenCalledWith({
      nombre: 'Nuevo Proveedor',
      cuit: '30616874582',
      telefono: '123456789',
      email: 'test@test.com',
      direccion: 'Calle 123',
    })
  })

  it('calls onCancel when clicking cancel', () => {
    const onCancel = vi.fn()
    render(
      <ProveedorForm
        proveedor={null}
        onSubmit={vi.fn()}
        onCancel={onCancel}
        loading={false}
        error={null}
      />,
    )
    fireEvent.click(screen.getByText('Cancelar'))
    expect(onCancel).toHaveBeenCalled()
  })

  it('displays error banner', () => {
    render(
      <ProveedorForm
        proveedor={null}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
        loading={false}
        error="CUIT duplicado"
      />,
    )
    expect(screen.getByText('CUIT duplicado')).toBeInTheDocument()
  })

  it('disables inputs when loading', () => {
    render(
      <ProveedorForm
        proveedor={null}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
        loading={true}
        error={null}
      />,
    )
    expect(screen.getByLabelText(/Nombre/)).toBeDisabled()
    expect(screen.getByText('Guardando...')).toBeInTheDocument()
  })
})
