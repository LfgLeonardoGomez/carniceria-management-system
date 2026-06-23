/**
 * Tests for RentabilidadCortesTable (Task 8.2).
 *
 * TDD cycle:
 *   RED — renders one row per cut; null margin → "no disponible" (not "0")
 *   TRIANGULATE — known margin; empty state; costo always present
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { CorteRentabilidadRow } from './types'

const rowFull: CorteRentabilidadRow = {
  tipo_corte: 'asado',
  producto_id: 'uuid-1',
  nombre_producto: 'Asado Premium',
  costo_por_kilo: '800.00',
  precio_venta_promedio: '1000.00',
  margen_por_kilo: '200.00',
  margen_porcentaje: '20.00',
}

const rowNoSales: CorteRentabilidadRow = {
  tipo_corte: 'vacio',
  producto_id: 'uuid-2',
  nombre_producto: 'Vacio',
  costo_por_kilo: '900.00',
  precio_venta_promedio: null,
  margen_por_kilo: null,
  margen_porcentaje: null,
}

describe('RentabilidadCortesTable', () => {
  it('renders one row per cut', async () => {
    const { RentabilidadCortesTable } = await import('./RentabilidadCortesTable')
    render(<RentabilidadCortesTable rows={[rowFull, rowNoSales]} />)

    const tipoCorteEls = screen.getAllByTestId('rentabilidad-corte-tipo')
    expect(tipoCorteEls).toHaveLength(2)
    expect(tipoCorteEls[0]).toHaveTextContent('asado')
    expect(tipoCorteEls[1]).toHaveTextContent('vacio')
  })

  it('renders null margin as "no disponible", not "0"', async () => {
    const { RentabilidadCortesTable } = await import('./RentabilidadCortesTable')
    render(<RentabilidadCortesTable rows={[rowNoSales]} />)

    const margenCells = screen.getAllByTestId('rentabilidad-corte-margen')
    expect(margenCells[0]).toHaveTextContent('no disponible')
    expect(margenCells[0]).not.toHaveTextContent('0')

    const precioCells = screen.getAllByTestId('rentabilidad-corte-precio')
    expect(precioCells[0]).toHaveTextContent('no disponible')
  })

  it('renders costo_por_kilo which is always present', async () => {
    const { RentabilidadCortesTable } = await import('./RentabilidadCortesTable')
    render(<RentabilidadCortesTable rows={[rowNoSales]} />)

    const costoCells = screen.getAllByTestId('rentabilidad-corte-costo')
    expect(costoCells[0]).not.toHaveTextContent('no disponible')
    expect(costoCells[0].textContent).toMatch(/900/)
  })

  it('renders known margin values when sales exist', async () => {
    const { RentabilidadCortesTable } = await import('./RentabilidadCortesTable')
    render(<RentabilidadCortesTable rows={[rowFull]} />)

    const margenCells = screen.getAllByTestId('rentabilidad-corte-margen')
    expect(margenCells[0]).not.toHaveTextContent('no disponible')
    expect(margenCells[0].textContent).toMatch(/20/)

    const precioCells = screen.getAllByTestId('rentabilidad-corte-precio')
    expect(precioCells[0].textContent).toMatch(/1000/)
  })

  it('renders empty state when rows is empty', async () => {
    const { RentabilidadCortesTable } = await import('./RentabilidadCortesTable')
    render(<RentabilidadCortesTable rows={[]} />)

    expect(screen.getByTestId('rentabilidad-corte-empty')).toBeInTheDocument()
  })
})
