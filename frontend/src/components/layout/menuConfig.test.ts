import { describe, it, expect } from 'vitest'
import {
  menuGroups,
  canSee,
  type MenuItem,
  type Role,
} from '@/components/layout/menuConfig'

const ALL_ROLES: Role[] = ['admin', 'encargado', 'cajero', 'vendedor']

const findItem = (path: string): MenuItem | undefined => {
  for (const group of menuGroups) {
    const item = group.items.find((i) => i.path === path)
    if (item) return item
  }
  return undefined
}

describe('menuConfig', () => {
  it('declares the 4 required sections', () => {
    const titles = menuGroups.map((g) => g.title)
    expect(titles).toContain('Operaciones')
    expect(titles).toContain('Catálogo')
    expect(titles).toContain('Gestión')
    expect(titles).toContain('Administración')
  })

  it('exposes the scope routes as menu items', () => {
    const expectedPaths = [
      '/',
      '/pos',
      '/productos',
      '/stock',
      '/compras',
      '/despostes',
      '/clientes',
      '/proveedores',
      '/cuentas-corrientes/:clienteId',
      '/caja',
      '/gastos',
      '/reportes',
      '/reportes/financieros',
      '/rentabilidad',
      '/usuarios',
      '/auditoria',
      '/configuracion/empresa',
      '/perfil',
    ]
    for (const path of expectedPaths) {
      expect(findItem(path), `missing menu item for path ${path}`).toBeDefined()
    }
  })

  it('every menu item has a non-empty roles array', () => {
    for (const group of menuGroups) {
      for (const item of group.items) {
        expect(item.roles.length, `${item.path} should declare roles`).toBeGreaterThan(0)
      }
    }
  })
})

describe('canSee', () => {
  it('admin sees every item that has admin in roles', () => {
    const item = findItem('/usuarios')!
    expect(canSee(item, 'admin')).toBe(true)
  })

  it('cajero does NOT see admin-only items (usuarios, config empresa, reportes financieros)', () => {
    const usuarios = findItem('/usuarios')!
    const config = findItem('/configuracion/empresa')!
    const reportesFin = findItem('/reportes/financieros')!
    const rentabilidad = findItem('/rentabilidad')!

    expect(canSee(usuarios, 'cajero')).toBe(false)
    expect(canSee(config, 'cajero')).toBe(false)
    expect(canSee(reportesFin, 'cajero')).toBe(false)
    expect(canSee(rentabilidad, 'cajero')).toBe(false)
  })

  it('cajero DOES see allowed items (dashboard, pos, clientes, cuentas-corrientes, caja, perfil)', () => {
    const dashboard = findItem('/')!
    const pos = findItem('/pos')!
    const clientes = findItem('/clientes')!
    const cc = findItem('/cuentas-corrientes/:clienteId')!
    const caja = findItem('/caja')!
    const perfil = findItem('/perfil')!

    expect(canSee(dashboard, 'cajero')).toBe(true)
    expect(canSee(pos, 'cajero')).toBe(true)
    expect(canSee(clientes, 'cajero')).toBe(true)
    expect(canSee(cc, 'cajero')).toBe(true)
    expect(canSee(caja, 'cajero')).toBe(true)
    expect(canSee(perfil, 'cajero')).toBe(true)
  })

  it('vendedor sees only minimal set (dashboard, pos, perfil)', () => {
    for (const group of menuGroups) {
      for (const item of group.items) {
        const visible = canSee(item, 'vendedor')
        const allowed = item.path === '/' || item.path === '/pos' || item.path === '/perfil'
        expect(visible, `vendedor visibility wrong for ${item.path}`).toBe(allowed)
      }
    }
  })

  it('encargado sees everything EXCEPT admin-only (usuarios, configuracion/empresa, auditoria)', () => {
    const usuarios = findItem('/usuarios')!
    const config = findItem('/configuracion/empresa')!
    const auditoria = findItem('/auditoria')!

    expect(canSee(usuarios, 'encargado')).toBe(false)
    expect(canSee(config, 'encargado')).toBe(false)
    expect(canSee(auditoria, 'encargado')).toBe(false)

    for (const group of menuGroups) {
      for (const item of group.items) {
        if (
          item.path === '/usuarios' ||
          item.path === '/configuracion/empresa' ||
          item.path === '/auditoria'
        ) {
          continue
        }
        expect(canSee(item, 'encargado'), `encargado should see ${item.path}`).toBe(true)
      }
    }
  })

  it('superadmin is mapped to admin (sees everything)', () => {
    const usuarios = findItem('/usuarios')!
    const config = findItem('/configuracion/empresa')!
    expect(canSee(usuarios, 'superadmin')).toBe(true)
    expect(canSee(config, 'superadmin')).toBe(true)
  })

  it('unknown role returns false (no leakage)', () => {
    const dashboard = findItem('/')!
    expect(canSee(dashboard, 'intruder')).toBe(false)
  })

  it('all defined roles resolve without throwing for every item', () => {
    for (const group of menuGroups) {
      for (const item of group.items) {
        for (const role of ALL_ROLES) {
          expect(() => canSee(item, role)).not.toThrow()
        }
      }
    }
  })
})
