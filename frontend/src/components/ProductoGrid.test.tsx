import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProductoGrid } from '@/components/ProductoGrid'
import type { Producto, CategoriaProducto } from '@/shared/types/producto'

const mockCategorias: CategoriaProducto[] = [
  { id: 'cat-1', empresa_id: 'emp-1', nombre: 'Carne vacuna', created_at: '', updated_at: '' },
]

const mockProductos: Producto[] = [
  {
    id: 'p1',
    empresa_id: 'emp-1',
    plu: '001',
    nombre: 'Asado',
    categoria_id: 'cat-1',
    precio_publico: '1500.0000',
    precio_mayorista: '1200.0000',
    costo_por_kilo: '900.0000',
    margen: '0.4000',
    stock_actual: '10.0000',
    stock_minimo: '2.0000',
    activo: true,
    created_at: '',
    updated_at: '',
  },
]

describe('ProductoGrid', () => {
  it('renders product rows', () => {
    render(
      <ProductoGrid
        productos={mockProductos}
        categorias={mockCategorias}
        onEdit={vi.fn()}
        onToggleActivo={vi.fn()}
        onSearch={vi.fn()}
        onFilterCategoria={vi.fn()}
        onFilterActivo={vi.fn()}
        search=""
        categoriaFilter=""
        activoFilter={true}
      />
    )

    expect(screen.getByText('Asado')).toBeInTheDocument()
    expect(screen.getByText('001')).toBeInTheDocument()
    expect(screen.getByText('40.00%')).toBeInTheDocument()
  })

  it('triggers search on input change', () => {
    const onSearch = vi.fn()
    render(
      <ProductoGrid
        productos={mockProductos}
        categorias={mockCategorias}
        onEdit={vi.fn()}
        onToggleActivo={vi.fn()}
        onSearch={onSearch}
        onFilterCategoria={vi.fn()}
        onFilterActivo={vi.fn()}
        search=""
        categoriaFilter=""
        activoFilter={true}
      />
    )

    const input = screen.getByPlaceholderText('Buscar por PLU o nombre...')
    fireEvent.change(input, { target: { value: 'Asado' } })
    expect(onSearch).toHaveBeenCalledWith('Asado')
  })

  it('shows desactivar button for active product', () => {
    render(
      <ProductoGrid
        productos={mockProductos}
        categorias={mockCategorias}
        onEdit={vi.fn()}
        onToggleActivo={vi.fn()}
        onSearch={vi.fn()}
        onFilterCategoria={vi.fn()}
        onFilterActivo={vi.fn()}
        search=""
        categoriaFilter=""
        activoFilter={true}
      />
    )

    expect(screen.getByText('Desactivar')).toBeInTheDocument()
  })
})
