import type { SVGProps } from 'react'

type IconProps = { className?: string } & Omit<SVGProps<SVGSVGElement>, 'className'>

const baseProps = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.75,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

export function HomeIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <path d="M3 12l9-9 9 9" />
      <path d="M5 10v10a1 1 0 001 1h3v-6h6v6h3a1 1 0 001-1V10" />
    </svg>
  )
}

export function ShoppingCartIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <circle cx="9" cy="20" r="1.5" />
      <circle cx="18" cy="20" r="1.5" />
      <path d="M2 3h2l2.4 12.3a2 2 0 002 1.7h8.6a2 2 0 002-1.7L21 7H6" />
    </svg>
  )
}

export function BoxIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <path d="M21 8l-9 4-9-4 9-4 9 4z" />
      <path d="M3 8v8l9 4 9-4V8" />
      <path d="M12 12v8" />
    </svg>
  )
}

export function WarehouseIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <path d="M3 21V9l9-6 9 6v12" />
      <path d="M3 21h18" />
      <path d="M9 21v-7h6v7" />
    </svg>
  )
}

export function TruckIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <path d="M3 7h11v10H3z" />
      <path d="M14 10h4l3 3v4h-7" />
      <circle cx="7" cy="18" r="1.5" />
      <circle cx="17" cy="18" r="1.5" />
    </svg>
  )
}

export function ScissorsIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <circle cx="6" cy="6" r="3" />
      <circle cx="6" cy="18" r="3" />
      <line x1="20" y1="4" x2="8.12" y2="15.88" />
      <line x1="14.47" y1="14.48" x2="20" y2="20" />
      <line x1="8.12" y1="8.12" x2="12" y2="12" />
    </svg>
  )
}

export function UsersIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 00-3-3.87" />
      <path d="M16 3.13a4 4 0 010 7.75" />
    </svg>
  )
}

export function AddressBookIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <path d="M6 4h12a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2z" />
      <circle cx="12" cy="12" r="3" />
      <line x1="12" y1="9" x2="12" y2="9.01" />
      <line x1="6" y1="9" x2="8" y2="9" />
      <line x1="6" y1="15" x2="8" y2="15" />
    </svg>
  )
}

export function CashIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <rect x="2" y="6" width="20" height="12" rx="2" />
      <circle cx="12" cy="12" r="3" />
      <path d="M6 12h.01M18 12h.01" />
    </svg>
  )
}

export function ReceiptIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <path d="M5 3h14v18l-3-2-3 2-3-2-3 2-2-2V3z" />
      <path d="M8 8h8M8 12h8M8 16h5" />
    </svg>
  )
}

export function ChartIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <line x1="4" y1="20" x2="4" y2="10" />
      <line x1="10" y1="20" x2="10" y2="4" />
      <line x1="16" y1="20" x2="16" y2="14" />
      <line x1="20" y1="20" x2="20" y2="8" />
      <line x1="2" y1="20" x2="22" y2="20" />
    </svg>
  )
}

export function TrendingUpIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <polyline points="3 17 9 11 13 15 21 7" />
      <polyline points="14 7 21 7 21 14" />
    </svg>
  )
}

export function CogIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z" />
    </svg>
  )
}

export function UserCogIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <circle cx="9" cy="8" r="4" />
      <path d="M2 21a7 7 0 0114 0" />
      <circle cx="18" cy="15" r="3" />
      <path d="M18 12v1.5M18 16.5V18M21 15h-1.5M16.5 15H15M20 13l-1 1M17 16l-1 1M20 17l-1-1M17 14l-1-1" />
    </svg>
  )
}

export function MenuIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  )
}

export function LogoutIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  )
}

export function ChevronLeftIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <polyline points="15 18 9 12 15 6" />
    </svg>
  )
}

export function ChevronRightIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <polyline points="9 18 15 12 9 6" />
    </svg>
  )
}

export function UserCircleIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="10" r="3" />
      <path d="M6.5 19a6 6 0 0111 0" />
    </svg>
  )
}

export function BellIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <path d="M6 8a6 6 0 0112 0c0 7 3 9 3 9H3s3-2 3-9" />
      <path d="M10 21a2 2 0 004 0" />
    </svg>
  )
}

export function ShieldCheckIcon({ className = 'w-5 h-5', ...rest }: IconProps) {
  return (
    <svg {...baseProps} className={className} {...rest}>
      <path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z" />
      <polyline points="9 12 11 14 15 10" />
    </svg>
  )
}
