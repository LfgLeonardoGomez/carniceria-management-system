import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { LoginLayout } from '@/components/layout/LoginLayout'

function renderLoginLayout(children: ReactNode = <div data-testid="login-children">LoginForm</div>) {
  return render(
    <MemoryRouter>
      <LoginLayout>{children}</LoginLayout>
    </MemoryRouter>,
  )
}

describe('LoginLayout', () => {
  it('renders the BASILE brand title', () => {
    renderLoginLayout()
    expect(screen.getByRole('heading', { name: 'BASILE' })).toBeInTheDocument()
  })

  it('renders children inside the card', () => {
    renderLoginLayout()
    expect(screen.getByTestId('login-children')).toBeInTheDocument()
    expect(screen.getByText('LoginForm')).toBeInTheDocument()
  })

  it('the card has the primary-600 top border accent class', () => {
    renderLoginLayout()
    const brand = screen.getByRole('heading', { name: 'BASILE' })
    const card = brand.closest('[data-testid="login-card"]') as HTMLElement
    expect(card).not.toBeNull()
    expect(card.className).toMatch(/border-primary-600/)
  })

  it('uses the surface-50 background', () => {
    renderLoginLayout()
    const brand = screen.getByRole('heading', { name: 'BASILE' })
    const wrapper = brand.closest('div[class*="min-h-screen"]') as HTMLElement
    expect(wrapper).not.toBeNull()
    expect(wrapper.className).toMatch(/bg-surface-50/)
  })

  it('does NOT render the AppLayout sidebar/header chrome', () => {
    renderLoginLayout()
    expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument()
    expect(screen.queryByTestId('header')).not.toBeInTheDocument()
  })

  it('uses shadow-card utility for elevated card', () => {
    renderLoginLayout()
    const brand = screen.getByRole('heading', { name: 'BASILE' })
    const card = brand.closest('[data-testid="login-card"]') as HTMLElement
    expect(card.className).toMatch(/shadow-card/)
  })
})
