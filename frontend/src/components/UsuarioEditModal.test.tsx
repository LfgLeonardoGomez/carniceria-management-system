import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { UsuarioEditModal } from '@/components/UsuarioEditModal'
import type { UsuarioPublic } from '@/shared/types/usuario'

const mockUsuario: UsuarioPublic = {
  id: 'u-1',
  nombre: 'Ana',
  apellido: 'García',
  email: 'ana@example.com',
  rol: 'Administrador',
  activo: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('UsuarioEditModal', () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined)
  const onCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders form with user data', () => {
    render(
      <UsuarioEditModal usuario={mockUsuario} onSubmit={onSubmit} onCancel={onCancel} loading={false} error={null} />
    )

    expect(screen.getByLabelText('Nombre')).toHaveValue('Ana')
    expect(screen.getByLabelText('Apellido')).toHaveValue('García')
    expect(screen.getByLabelText('Email')).toHaveValue('ana@example.com')
    expect(screen.getByLabelText('Estado actual')).toHaveValue('Activo')
  })

  it('calls onSubmit with updated data', async () => {
    render(
      <UsuarioEditModal usuario={mockUsuario} onSubmit={onSubmit} onCancel={onCancel} loading={false} error={null} />
    )

    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Ana María' } })
    fireEvent.change(screen.getByLabelText('Rol'), { target: { value: '96ccee1d-f141-5267-b275-9ddc692187e6' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        nombre: 'Ana María',
        apellido: 'García',
        email: 'ana@example.com',
        rol_id: '96ccee1d-f141-5267-b275-9ddc692187e6',
      })
    })
  })

  it('shows email validation error for invalid email', async () => {
    render(
      <UsuarioEditModal usuario={mockUsuario} onSubmit={onSubmit} onCancel={onCancel} loading={false} error={null} />
    )

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'bad-email' } })
    fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }))

    await waitFor(() => {
      expect(screen.getByText('Email inválido')).toBeInTheDocument()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('shows backend error when provided', () => {
    render(
      <UsuarioEditModal usuario={mockUsuario} onSubmit={onSubmit} onCancel={onCancel} loading={false} error="Error del servidor" />
    )

    expect(screen.getByText('Error del servidor')).toBeInTheDocument()
  })

  it('calls onCancel when cancel button clicked', () => {
    render(
      <UsuarioEditModal usuario={mockUsuario} onSubmit={onSubmit} onCancel={onCancel} loading={false} error={null} />
    )

    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(onCancel).toHaveBeenCalled()
  })
})
