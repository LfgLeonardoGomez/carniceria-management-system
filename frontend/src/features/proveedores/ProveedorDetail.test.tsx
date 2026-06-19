import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProveedorDetail } from '@/features/proveedores/ProveedorDetail'
import type { Proveedor } from '@/shared/types/proveedor'

const mockProveedor: Proveedor = {
  id: '1',
  empresa_id: 'e1',
  nombre: 'Carnes del Sur',
  cuit: '30616874582',
  telefono: '123456789',
  email: 'contacto@carne.com',
  direccion: 'Av Siempre Viva 123',
  activo: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('ProveedorDetail', () => {
  it('renders proveedor data', () => {
    render(
      <ProveedorDetail
        proveedor={mockProveedor}
        historial={{ items: [], total: 0 }}
        loading={false}
        onBack={vi.fn()}
        onEdit={vi.fn()}
        canMutate={true}
      />,
    )
    expect(screen.getByText('Carnes del Sur')).toBeInTheDocument()
    expect(screen.getByText('30616874582')).toBeInTheDocument()
    expect(screen.getByText('123456789')).toBeInTheDocument()
    expect(screen.getByText('contacto@carne.com')).toBeInTheDocument()
    expect(screen.getByText('Av Siempre Viva 123')).toBeInTheDocument()
    expect(screen.getByText('Activo')).toBeInTheDocument()
  })

  it('shows edit button when canMutate is true', () => {
    render(
      <ProveedorDetail
        proveedor={mockProveedor}
        historial={{ items: [], total: 0 }}
        loading={false}
        onBack={vi.fn()}
        onEdit={vi.fn()}
        canMutate={true}
      />,
    )
    expect(screen.getByText('Editar')).toBeInTheDocument()
  })

  it('hides edit button when canMutate is false', () => {
    render(
      <ProveedorDetail
        proveedor={mockProveedor}
        historial={{ items: [], total: 0 }}
        loading={false}
        onBack={vi.fn()}
        onEdit={vi.fn()}
        canMutate={false}
      />,
    )
    expect(screen.queryByText('Editar')).not.toBeInTheDocument()
  })

  it('calls onBack when clicking back button', () => {
    const onBack = vi.fn()
    render(
      <ProveedorDetail
        proveedor={mockProveedor}
        historial={{ items: [], total: 0 }}
        loading={false}
        onBack={onBack}
        onEdit={vi.fn()}
        canMutate={true}
      />,
    )
    fireEvent.click(screen.getByText('← Volver'))
    expect(onBack).toHaveBeenCalled()
  })

  it('calls onEdit when clicking edit button', () => {
    const onEdit = vi.fn()
    render(
      <ProveedorDetail
        proveedor={mockProveedor}
        historial={{ items: [], total: 0 }}
        loading={false}
        onBack={vi.fn()}
        onEdit={onEdit}
        canMutate={true}
      />,
    )
    fireEvent.click(screen.getByText('Editar'))
    expect(onEdit).toHaveBeenCalled()
  })

  it('shows empty historial message', () => {
    render(
      <ProveedorDetail
        proveedor={mockProveedor}
        historial={{ items: [], total: 0 }}
        loading={false}
        onBack={vi.fn()}
        onEdit={vi.fn()}
        canMutate={true}
      />,
    )
    expect(screen.getByText('Sin compras registradas')).toBeInTheDocument()
  })

  it('shows loading state for historial', () => {
    render(
      <ProveedorDetail
        proveedor={mockProveedor}
        historial={{ items: [], total: 0 }}
        loading={true}
        onBack={vi.fn()}
        onEdit={vi.fn()}
        canMutate={true}
      />,
    )
    expect(screen.getByText('Cargando historial...')).toBeInTheDocument()
  })

  it('renders historial items when available', () => {
    const historial = {
      items: [
        {
          id: 'c1',
          fecha: '2024-06-01',
          cantidad_medias_reses: 2,
          peso_total: '150.000',
          costo_total: '450000.00',
          costo_por_kilo: '3000.00',
          observaciones: null,
        },
      ],
      total: 1,
    }
    render(
      <ProveedorDetail
        proveedor={mockProveedor}
        historial={historial}
        loading={false}
        onBack={vi.fn()}
        onEdit={vi.fn()}
        canMutate={true}
      />,
    )
    expect(screen.getByText('2024-06-01')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('150.000')).toBeInTheDocument()
    expect(screen.getByText('450000.00')).toBeInTheDocument()
    expect(screen.getByText('3000.00')).toBeInTheDocument()
  })
})
