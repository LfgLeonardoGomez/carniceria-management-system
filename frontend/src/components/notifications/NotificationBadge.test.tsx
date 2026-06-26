import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { NotificationBadge } from '@/components/notifications/NotificationBadge'

const { mockUnreadCount, mockOpen, setMockState } = vi.hoisted(() => {
  const state = { unreadCount: 0, open: false }
  return {
    mockUnreadCount: () => state.unreadCount,
    mockOpen: () => state.open,
    setMockState: (next: Partial<{ unreadCount: number; open: boolean }>) => {
      if (next.unreadCount !== undefined) state.unreadCount = next.unreadCount
      if (next.open !== undefined) state.open = next.open
    },
  }
})

vi.mock('@/stores/notificacionStore', () => ({
  useNotificacionStore: (selector?: (s: { unreadCount: number }) => unknown) => {
    const state = { unreadCount: state_unreadCount() }
    return selector ? selector(state) : state
  },
}))

function state_unreadCount(): number {
  return mockUnreadCount()
}

vi.mock('@/components/notifications/NotificationPanel', () => ({
  NotificationPanel: () => <div data-testid="notification-panel-mock">panel</div>,
}))

describe('NotificationBadge', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setMockState({ unreadCount: 0, open: false })
  })

  it('muestra el contador de no leídas cuando hay > 0', () => {
    setMockState({ unreadCount: 5 })
    render(<NotificationBadge onToggle={vi.fn()} open={false} />)
    const badge = screen.getByTestId('notification-badge-count')
    expect(badge).toHaveTextContent('5')
  })

  it('no muestra el contador cuando no hay no leídas', () => {
    setMockState({ unreadCount: 0 })
    render(<NotificationBadge onToggle={vi.fn()} open={false} />)
    expect(screen.queryByTestId('notification-badge-count')).not.toBeInTheDocument()
  })

  it('muestra "99+" cuando el contador supera 99', () => {
    setMockState({ unreadCount: 150 })
    render(<NotificationBadge onToggle={vi.fn()} open={false} />)
    expect(screen.getByTestId('notification-badge-count')).toHaveTextContent('99+')
  })

  it('llama a onToggle al hacer click', () => {
    setMockState({ unreadCount: 3 })
    const onToggle = vi.fn()
    render(<NotificationBadge onToggle={onToggle} open={false} />)
    fireEvent.click(screen.getByRole('button', { name: /notificaciones/i }))
    expect(onToggle).toHaveBeenCalledTimes(1)
  })

  it('indica visualmente cuando el panel está abierto', () => {
    setMockState({ unreadCount: 1 })
    const { rerender } = render(<NotificationBadge onToggle={vi.fn()} open={false} />)
    const btn1 = screen.getByRole('button', { name: /notificaciones/i })
    expect(btn1).toHaveAttribute('aria-expanded', 'false')

    rerender(<NotificationBadge onToggle={vi.fn()} open={true} />)
    const btn2 = screen.getByRole('button', { name: /notificaciones/i })
    expect(btn2).toHaveAttribute('aria-expanded', 'true')
  })
})
