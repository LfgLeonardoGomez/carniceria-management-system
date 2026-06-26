import type { ReactNode } from 'react'

interface LoginLayoutProps {
  children: ReactNode
}

export function LoginLayout({ children }: LoginLayoutProps) {
  return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center p-4">
      <div
        data-testid="login-card"
        className="w-full max-w-md bg-white rounded-lg shadow-card border-t-4 border-primary-600 p-8"
      >
        <h1 className="text-2xl font-bold text-primary-600 mb-6">BASILE</h1>
        {children}
      </div>
    </div>
  )
}
