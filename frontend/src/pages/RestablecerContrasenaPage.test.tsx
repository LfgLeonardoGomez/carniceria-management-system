import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { RestablecerContrasenaPage } from '@/pages/RestablecerContrasenaPage'
import * as api from '@/features/auth/api'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock('@/features/auth/api')

function renderRestablecer(initialEntries: string[] = ['/restablecer-contrasena?token=valid-token']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="/restablecer-contrasena" element={<RestablecerContrasenaPage />} />
        <Route path="/login" element={<div>Login</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

// ---------------------------------------------------------------------------
// Task 3.4 — RestablecerContrasenaPage tests
// ---------------------------------------------------------------------------
describe('RestablecerContrasenaPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders new password and confirmation fields with token', () => {
    renderRestablecer()
    expect(screen.getByLabelText('Nueva contraseña')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirmar contraseña')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /restablecer contraseña/i })).toBeInTheDocument()
  })

  it('submits new password and redirects to login on success', async () => {
    vi.mocked(api.reset).mockResolvedValue(undefined)

    renderRestablecer()

    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'newpassword123' } })
    fireEvent.change(screen.getByLabelText('Confirmar contraseña'), { target: { value: 'newpassword123' } })
    fireEvent.click(screen.getByRole('button', { name: /restablecer contraseña/i }))

    await waitFor(() => {
      expect(api.reset).toHaveBeenCalledWith({ token: 'valid-token', new_password: 'newpassword123' })
    })

    await waitFor(() => {
      expect(screen.getByText('Login')).toBeInTheDocument()
    })
  })

  it('shows validation error when passwords do not match', async () => {
    vi.mocked(api.reset).mockResolvedValue(undefined)

    renderRestablecer()

    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'newpassword123' } })
    fireEvent.change(screen.getByLabelText('Confirmar contraseña'), { target: { value: 'differentpass' } })
    fireEvent.click(screen.getByRole('button', { name: /restablecer contraseña/i }))

    await waitFor(() => {
      expect(screen.getByText('Las contraseñas no coinciden')).toBeInTheDocument()
    })
    expect(api.reset).not.toHaveBeenCalled()
  })

  it('shows validation error when password is too short', async () => {
    vi.mocked(api.reset).mockResolvedValue(undefined)

    renderRestablecer()

    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'short' } })
    fireEvent.change(screen.getByLabelText('Confirmar contraseña'), { target: { value: 'short' } })
    fireEvent.click(screen.getByRole('button', { name: /restablecer contraseña/i }))

    await waitFor(() => {
      expect(screen.getByText('La contraseña debe tener al menos 8 caracteres')).toBeInTheDocument()
    })
    expect(api.reset).not.toHaveBeenCalled()
  })

  it('shows error for expired or invalid token', async () => {
    const error = new Error('Invalid token') as Error & { response?: { data: { detail: string } } }
    error.response = { data: { detail: 'El enlace es inválido o ha expirado' } }
    vi.mocked(api.reset).mockRejectedValue(error)

    renderRestablecer()

    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'newpassword123' } })
    fireEvent.change(screen.getByLabelText('Confirmar contraseña'), { target: { value: 'newpassword123' } })
    fireEvent.click(screen.getByRole('button', { name: /restablecer contraseña/i }))

    await waitFor(() => {
      expect(screen.getByText('El enlace es inválido o ha expirado')).toBeInTheDocument()
    })

    expect(screen.getByText(/solicitar un nuevo enlace/i)).toBeInTheDocument()
  })

  it('shows error when token is missing from URL', () => {
    renderRestablecer(['/restablecer-contrasena'])
    expect(screen.getByRole('alert').textContent).toMatch(/El enlace es inválido o incompleto/i)
    expect(screen.getByText(/solicitar un nuevo enlace/i)).toBeInTheDocument()
  })
})
