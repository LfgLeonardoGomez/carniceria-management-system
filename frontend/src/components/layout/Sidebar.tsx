import { NavLink } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { canSee, menuGroups } from '@/components/layout/menuConfig'
import { ChevronLeftIcon, ChevronRightIcon } from '@/components/layout/icons'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

const SIDEBAR_WIDTH_EXPANDED = 'w-60'
const SIDEBAR_WIDTH_COLLAPSED = 'w-16'

function resolvePath(path: string): string {
  if (path.includes(':')) {
    return path.split('/:')[0] || '/'
  }
  return path
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const rol = useAuthStore((s) => s.user?.rol)

  return (
    <aside
      role="complementary"
      aria-label="Navegación principal"
      data-testid="sidebar"
      data-collapsed={collapsed ? 'true' : 'false'}
      className={`flex flex-col h-full bg-white border-r border-surface-200 transition-all duration-200 ${
        collapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_EXPANDED
      }`}
    >
      <nav className="flex-1 overflow-y-auto py-4" aria-label="Menú principal">
        {menuGroups.map((group) => {
          const visibleItems = group.items.filter((item) => canSee(item, rol ?? ''))
          if (visibleItems.length === 0) return null

          return (
            <div key={group.title} className="mb-6">
              {!collapsed && (
                <h3 className="px-4 mb-2 text-xs uppercase tracking-wider text-surface-500 font-semibold">
                  {group.title}
                </h3>
              )}
              <ul className="space-y-1 px-2">
                {visibleItems.map((item) => {
                  const Icon = item.icon
                  return (
                    <li key={item.path}>
                      <NavLink
                        to={resolvePath(item.path)}
                        end={item.path === '/'}
                        title={collapsed ? item.label : undefined}
                        aria-label={item.label}
                        className={({ isActive }) =>
                          `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                            collapsed ? 'justify-center' : ''
                          } ${
                            isActive
                              ? 'bg-primary-50 text-primary-700'
                              : 'text-surface-700 hover:bg-surface-100'
                          }`
                        }
                      >
                        <Icon className="w-5 h-5 flex-shrink-0" />
                        {!collapsed && <span className="truncate">{item.label}</span>}
                      </NavLink>
                    </li>
                  )
                })}
              </ul>
            </div>
          )
        })}
      </nav>

      <div className="border-t border-surface-200 p-2">
        <button
          type="button"
          onClick={onToggle}
          aria-label={collapsed ? 'Expandir sidebar' : 'Colapsar sidebar'}
          className={`w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-surface-600 hover:bg-surface-100 rounded-md transition-colors ${
            collapsed ? 'justify-center' : ''
          }`}
        >
          {collapsed ? (
            <ChevronRightIcon className="w-5 h-5" />
          ) : (
            <>
              <ChevronLeftIcon className="w-5 h-5" />
              <span>Colapsar</span>
            </>
          )}
        </button>
      </div>
    </aside>
  )
}
