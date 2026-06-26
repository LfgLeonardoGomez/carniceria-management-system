import type { ComponentType } from 'react'
import {
  HomeIcon,
  ShoppingCartIcon,
  BoxIcon,
  WarehouseIcon,
  TruckIcon,
  ScissorsIcon,
  UsersIcon,
  AddressBookIcon,
  CashIcon,
  ReceiptIcon,
  ChartIcon,
  TrendingUpIcon,
  CogIcon,
  UserCogIcon,
  UserCircleIcon,
  ShieldCheckIcon,
} from '@/components/layout/icons'

export type Role = 'admin' | 'encargado' | 'cajero' | 'vendedor'

export interface MenuItem {
  label: string
  path: string
  icon: ComponentType<{ className?: string }>
  roles: Role[]
}

export interface MenuGroup {
  title: string
  items: MenuItem[]
}

export const menuGroups: MenuGroup[] = [
  {
    title: 'Operaciones',
    items: [
      { label: 'Dashboard', path: '/', icon: HomeIcon, roles: ['admin', 'encargado', 'cajero', 'vendedor'] },
      { label: 'Venta', path: '/pos', icon: ShoppingCartIcon, roles: ['admin', 'encargado', 'cajero', 'vendedor'] },
      { label: 'Caja', path: '/caja', icon: CashIcon, roles: ['admin', 'encargado', 'cajero'] },
      { label: 'Gastos', path: '/gastos', icon: ReceiptIcon, roles: ['admin', 'encargado'] },
    ],
  },
  {
    title: 'Catálogo',
    items: [
      { label: 'Productos', path: '/productos', icon: BoxIcon, roles: ['admin', 'encargado'] },
      { label: 'Stock', path: '/stock', icon: WarehouseIcon, roles: ['admin', 'encargado'] },
      { label: 'Compras', path: '/compras', icon: TruckIcon, roles: ['admin', 'encargado'] },
      { label: 'Despostes', path: '/despostes', icon: ScissorsIcon, roles: ['admin', 'encargado'] },
    ],
  },
  {
    title: 'Gestión',
    items: [
      { label: 'Clientes', path: '/clientes', icon: UsersIcon, roles: ['admin', 'encargado', 'cajero'] },
      { label: 'Proveedores', path: '/proveedores', icon: AddressBookIcon, roles: ['admin', 'encargado'] },
      { label: 'Cuentas Corrientes', path: '/cuentas-corrientes/:clienteId', icon: AddressBookIcon, roles: ['admin', 'encargado', 'cajero'] },
      { label: 'Reportes', path: '/reportes', icon: ChartIcon, roles: ['admin', 'encargado'] },
      { label: 'Reportes Financieros', path: '/reportes/financieros', icon: ChartIcon, roles: ['admin', 'encargado'] },
      { label: 'Rentabilidad', path: '/rentabilidad', icon: TrendingUpIcon, roles: ['admin', 'encargado'] },
    ],
  },
  {
    title: 'Administración',
    items: [
      { label: 'Usuarios', path: '/usuarios', icon: UserCogIcon, roles: ['admin'] },
      { label: 'Auditoría', path: '/auditoria', icon: ShieldCheckIcon, roles: ['admin'] },
      { label: 'Configuración Empresa', path: '/configuracion/empresa', icon: CogIcon, roles: ['admin'] },
      { label: 'Perfil', path: '/perfil', icon: UserCircleIcon, roles: ['admin', 'encargado', 'cajero', 'vendedor'] },
    ],
  },
]

const ROLE_ALIASES: Record<string, Role> = {
  superadmin: 'admin',
}

export function canSee(item: MenuItem, userRol: string): boolean {
  const role: Role = ROLE_ALIASES[userRol] ?? (userRol as Role)
  return item.roles.includes(role)
}
