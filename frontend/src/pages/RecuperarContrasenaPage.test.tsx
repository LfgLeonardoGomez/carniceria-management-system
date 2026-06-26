import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { RecuperarContrasenaPage } from '@/pages/RecuperarContrasenaPage'
import * as api from '@/features/auth/api'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock('@/features/auth/api')

function renderRecuperar() {
  return render(
    <MemoryRouter initialEntries={['/recuperar-contrasena']}>
      <Routes>
        <Route path="/recuperar-contrasena" element={<RecuperarContrasenaPage />} />
        <Route path="/login" element={<div>Login</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

// ---------------------------------------------------------------------------
// Task 2.3 — RecuperarContrasenaPage tests
// ---------------------------------------------------------------------------
describe('RecuperarContrasenaPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders email field and submit button', () => {
    renderRecuperar()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /enviar instrucciones/i })).toBeInTheDocument()
  })

  it('submits email and shows success message', async () => {
    vi.mocked(api.recover).mockResolvedValue(undefined)

    renderRecuperar()

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } })
    fireEvent.click(screen.getByRole('button', { name: /enviar instrucciones/i }))

    await waitFor(() => {
      expect(api.recover).toHaveBeenCalledWith({ email: 'user@example.com' })
    })

    await waitFor(() => {
      expect(screen.getByText(/revisá tu correo/i)).toBeInTheDocument()
    })
  })

  it('shows error message on API failure', async () => {
    const error = new Error('Fail') as Error & { response?: { data: { detail: string } } }
    error.response = { data: { detail: 'Error al procesar la solicitud' } }
    vi.mocked(api.recover).mockRejectedValue(error)

    renderRecuperar()

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'user@example.com' } })
    fireEvent.click(screen.getByRole('button', { name: /enviar instrucciones/i }))

    await waitFor(() => {
      expect(screen.getByText('Error al procesar la solicitud')).toBeInTheDocument()
    })
  })

  it('shows validation error for invalid email format', async () => {
    vi.mocked(api.recover).mockResolvedValue(undefined)

    renderRecuperar()

    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'not-an-email' } })
    fireEvent.click(screen.getByRole('button', { name: /enviar instrucciones/i }))

    await waitFor(() => {
      expect(screen.getByText(/ingresá un email válido/i)).toBeInTheDocument()
    })
    expect(api.recover).not.toHaveBeenCalled()
  })

  it('navigates back to login page', () => {
    renderRecuperar()
    fireEvent.click(screen.getByText(/volver al login/i))
    expect(screen.getByText('Login')).toBeInTheDocument()
  })
})
