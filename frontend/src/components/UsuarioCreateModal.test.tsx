import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { UsuarioCreateModal } from '@/components/UsuarioCreateModal'

describe('UsuarioCreateModal', () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined)
  const onCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders form fields', () => {
    render(
      <UsuarioCreateModal onSubmit={onSubmit} onCancel={onCancel} loading={false} error={null} />
    )

    expect(screen.getByLabelText('Nombre')).toBeInTheDocument()
    expect(screen.getByLabelText('Apellido')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Rol')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /crear/i })).toBeInTheDocument()
  })

  it('calls onSubmit with form data', async () => {
    render(
      <UsuarioCreateModal onSubmit={onSubmit} onCancel={onCancel} loading={false} error={null} />
    )

    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Juan' } })
    fireEvent.change(screen.getByLabelText('Apellido'), { target: { value: 'Pérez' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'juan@example.com' } })
    fireEvent.change(screen.getByLabelText('Rol'), { target: { value: '9d1f08ec-a0a9-5fbc-aaa6-a63ec0cbb704' } })
    fireEvent.click(screen.getByRole('button', { name: /crear/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        nombre: 'Juan',
        apellido: 'Pérez',
        email: 'juan@example.com',
        rol_id: '9d1f08ec-a0a9-5fbc-aaa6-a63ec0cbb704',
      })
    })
  })

  it('shows email validation error for invalid email', async () => {
    render(
      <UsuarioCreateModal onSubmit={onSubmit} onCancel={onCancel} loading={false} error={null} />
    )

    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Juan' } })
    fireEvent.change(screen.getByLabelText('Apellido'), { target: { value: 'Pérez' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'not-an-email' } })
    fireEvent.change(screen.getByLabelText('Rol'), { target: { value: '9d1f08ec-a0a9-5fbc-aaa6-a63ec0cbb704' } })
    fireEvent.click(screen.getByRole('button', { name: /crear/i }))

    await waitFor(() => {
      expect(screen.getByText('Email inválido')).toBeInTheDocument()
    })
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('shows backend error when provided', () => {
    render(
      <UsuarioCreateModal onSubmit={onSubmit} onCancel={onCancel} loading={false} error="Email ya registrado" />
    )

    expect(screen.getByText('Email ya registrado')).toBeInTheDocument()
  })

  it('calls onCancel when cancel button clicked', () => {
    render(
      <UsuarioCreateModal onSubmit={onSubmit} onCancel={onCancel} loading={false} error={null} />
    )

    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(onCancel).toHaveBeenCalled()
  })

  it('disables submit when loading', () => {
    render(
      <UsuarioCreateModal onSubmit={onSubmit} onCancel={onCancel} loading={true} error={null} />
    )

    expect(screen.getByRole('button', { name: /creando/i })).toBeDisabled()
  })
})
