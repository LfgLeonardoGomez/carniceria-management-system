/**
 * Tests for RentabilidadProductosTable (Task 8.1).
 *
 * TDD cycle:
 *   RED — renders one row per product; null margin → "no disponible" (not "0")
 *   TRIANGULATE — known margin renders; empty state; toggle controls present
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { ProductoRentabilidadRow } from './types'

const rowFull: ProductoRentabilidadRow = {
  producto_id: 'uuid-1',
  nombre: 'Asado',
  ventas: '1000.00',
  ganancia: '400.00',
  margen_porcentaje: '40.00',
}

const rowNullMargin: ProductoRentabilidadRow = {
  producto_id: 'uuid-2',
  nombre: 'Molida',
  ventas: '500.00',
  ganancia: null,
  margen_porcentaje: null,
}

describe('RentabilidadProductosTable', () => {
  it('renders one row per product', async () => {
    const { RentabilidadProductosTable } = await import('./RentabilidadProductosTable')
    render(
      <RentabilidadProductosTable
        rows={[rowFull, rowNullMargin]}
        orden="mayor"
        onOrdenChange={() => undefined}
      />
    )

    const nombres = screen.getAllByTestId('rentabilidad-prod-nombre')
    expect(nombres).toHaveLength(2)
    expect(nombres[0]).toHaveTextContent('Asado')
    expect(nombres[1]).toHaveTextContent('Molida')
  })

  it('renders null margin as "no disponible", not "0"', async () => {
    const { RentabilidadProductosTable } = await import('./RentabilidadProductosTable')
    render(
      <RentabilidadProductosTable
        rows={[rowNullMargin]}
        orden="mayor"
        onOrdenChange={() => undefined}
      />
    )

    const margenCells = screen.getAllByTestId('rentabilidad-prod-margen')
    expect(margenCells[0]).toHaveTextContent('no disponible')
    expect(margenCells[0]).not.toHaveTextContent('0')

    const gananciaCells = screen.getAllByTestId('rentabilidad-prod-ganancia')
    expect(gananciaCells[0]).toHaveTextContent('no disponible')
  })

  it('renders known margin values correctly', async () => {
    const { RentabilidadProductosTable } = await import('./RentabilidadProductosTable')
    render(
      <RentabilidadProductosTable
        rows={[rowFull]}
        orden="mayor"
        onOrdenChange={() => undefined}
      />
    )

    const margenCells = screen.getAllByTestId('rentabilidad-prod-margen')
    expect(margenCells[0]).not.toHaveTextContent('no disponible')
    expect(margenCells[0].textContent).toMatch(/40/)

    const ventasCells = screen.getAllByTestId('rentabilidad-prod-ventas')
    expect(ventasCells[0].textContent).toMatch(/1000/)
  })

  it('renders empty state when rows is empty', async () => {
    const { RentabilidadProductosTable } = await import('./RentabilidadProductosTable')
    render(
      <RentabilidadProductosTable
        rows={[]}
        orden="mayor"
        onOrdenChange={() => undefined}
      />
    )

    expect(screen.getByTestId('rentabilidad-prod-empty')).toBeInTheDocument()
  })

  it('renders the mayor/menor toggle controls', async () => {
    const { RentabilidadProductosTable } = await import('./RentabilidadProductosTable')
    render(
      <RentabilidadProductosTable
        rows={[rowFull]}
        orden="mayor"
        onOrdenChange={() => undefined}
      />
    )

    expect(screen.getByTestId('toggle-orden-mayor')).toBeInTheDocument()
    expect(screen.getByTestId('toggle-orden-menor')).toBeInTheDocument()
  })
})
