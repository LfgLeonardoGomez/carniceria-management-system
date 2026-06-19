import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProveedoresGrid } from '@/features/proveedores/ProveedoresGrid'
import type { Proveedor } from '@/shared/types/proveedor'

const mockProveedores: Proveedor[] = [
  {
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
  },
  {
    id: '2',
    empresa_id: 'e1',
    nombre: 'Pollos del Norte',
    cuit: null,
    telefono: null,
    email: null,
    direccion: null,
    activo: true,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: '3',
    empresa_id: 'e1',
    nombre: 'Inactivo SA',
    cuit: null,
    telefono: null,
    email: null,
    direccion: null,
    activo: false,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
  },
]

describe('ProveedoresGrid', () => {
  it('renders proveedores list', () => {
    render(
      <ProveedoresGrid
        proveedores={mockProveedores}
        total={3}
        loading={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onSearch={vi.fn()}
        onNavigate={vi.fn()}
        search=""
        canMutate={true}
      />,
    )
    expect(screen.getByText('Carnes del Sur')).toBeInTheDocument()
    expect(screen.getByText('Pollos del Norte')).toBeInTheDocument()
    expect(screen.getByText('Inactivo SA')).toBeInTheDocument()
    expect(screen.getByText('Total: 3 proveedores')).toBeInTheDocument()
  })

  it('calls onSearch when typing in search input', () => {
    const onSearch = vi.fn()
    render(
      <ProveedoresGrid
        proveedores={mockProveedores}
        total={3}
        loading={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onSearch={onSearch}
        onNavigate={vi.fn()}
        search=""
        canMutate={true}
      />,
    )
    const input = screen.getByPlaceholderText('Buscar por nombre...')
    fireEvent.change(input, { target: { value: 'carne' } })
    expect(onSearch).toHaveBeenCalledWith('carne')
  })

  it('calls onNavigate when clicking a row', () => {
    const onNavigate = vi.fn()
    render(
      <ProveedoresGrid
        proveedores={mockProveedores}
        total={3}
        loading={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onSearch={vi.fn()}
        onNavigate={onNavigate}
        search=""
        canMutate={true}
      />,
    )
    const row = screen.getByText('Carnes del Sur').closest('tr')
    fireEvent.click(row!)
    expect(onNavigate).toHaveBeenCalledWith(mockProveedores[0])
  })

  it('calls onEdit when clicking edit button', () => {
    const onEdit = vi.fn()
    render(
      <ProveedoresGrid
        proveedores={mockProveedores}
        total={3}
        loading={false}
        onEdit={onEdit}
        onDelete={vi.fn()}
        onSearch={vi.fn()}
        onNavigate={vi.fn()}
        search=""
        canMutate={true}
      />,
    )
    const editButtons = screen.getAllByText('Editar')
    fireEvent.click(editButtons[0])
    expect(onEdit).toHaveBeenCalledWith(mockProveedores[0])
  })

  it('shows confirm modal on delete', () => {
    const onDelete = vi.fn()
    render(
      <ProveedoresGrid
        proveedores={mockProveedores}
        total={3}
        loading={false}
        onEdit={vi.fn()}
        onDelete={onDelete}
        onSearch={vi.fn()}
        onNavigate={vi.fn()}
        search=""
        canMutate={true}
      />,
    )
    const deleteButtons = screen.getAllByText('Desactivar')
    fireEvent.click(deleteButtons[0])
    expect(screen.getByText(/¿Desactivar proveedor/)).toBeInTheDocument()
    expect(screen.getByText('Carnes del Sur', { selector: 'strong' })).toBeInTheDocument()
  })

  it('calls onDelete when confirming delete', () => {
    const onDelete = vi.fn()
    render(
      <ProveedoresGrid
        proveedores={mockProveedores}
        total={3}
        loading={false}
        onEdit={vi.fn()}
        onDelete={onDelete}
        onSearch={vi.fn()}
        onNavigate={vi.fn()}
        search=""
        canMutate={true}
      />,
    )
    const deleteButtons = screen.getAllByText('Desactivar')
    fireEvent.click(deleteButtons[0])
    const confirmButton = screen.getByText('Desactivar', { selector: 'button.danger' })
    fireEvent.click(confirmButton)
    expect(onDelete).toHaveBeenCalledWith(mockProveedores[0])
  })

  it('does not show action buttons when canMutate is false', () => {
    render(
      <ProveedoresGrid
        proveedores={mockProveedores}
        total={3}
        loading={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onSearch={vi.fn()}
        onNavigate={vi.fn()}
        search=""
        canMutate={false}
      />,
    )
    expect(screen.queryByText('Editar')).not.toBeInTheDocument()
    expect(screen.queryByText('Desactivar')).not.toBeInTheDocument()
  })

  it('shows empty state when no proveedores', () => {
    render(
      <ProveedoresGrid
        proveedores={[]}
        total={0}
        loading={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onSearch={vi.fn()}
        onNavigate={vi.fn()}
        search=""
        canMutate={true}
      />,
    )
    expect(screen.getByText('No hay proveedores')).toBeInTheDocument()
  })
})
