import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ClientesGrid } from '@/features/clientes/ClientesGrid'
import type { Cliente } from '@/shared/types/cliente'

const mockClientes: Cliente[] = [
  {
    id: 'c1',
    empresa_id: 'emp-1',
    nombre: 'Carlos',
    apellido: 'Gómez',
    razon_social: null,
    cuit: '20123456786',
    telefono: null,
    email: null,
    direccion: null,
    tipo_cliente: 'mayorista',
    limite_cuenta_corriente: '0.0000',
    saldo_actual: '1500.0000',
    activo: true,
    created_at: '',
    updated_at: '',
  },
  {
    id: 'c2',
    empresa_id: 'emp-1',
    nombre: 'Ana',
    apellido: 'Pérez',
    razon_social: null,
    cuit: null,
    telefono: null,
    email: null,
    direccion: null,
    tipo_cliente: 'publico_general',
    limite_cuenta_corriente: '0.0000',
    saldo_actual: '0.0000',
    activo: true,
    created_at: '',
    updated_at: '',
  },
]

describe('ClientesGrid', () => {
  it('renders client rows', () => {
    render(
      <ClientesGrid
        clientes={mockClientes}
        total={2}
        loading={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onSearch={vi.fn()}
        onFilterTipo={vi.fn()}
        onNavigate={vi.fn()}
        search=""
        tipoFilter=""
        canMutate={true}
      />
    )

    expect(screen.getByText('Carlos')).toBeInTheDocument()
    expect(screen.getByText('Ana')).toBeInTheDocument()
    expect(screen.getByText('mayorista')).toBeInTheDocument()
    expect(screen.getByText('1500.0000')).toBeInTheDocument()
  })

  it('triggers search on input change', () => {
    const onSearch = vi.fn()
    render(
      <ClientesGrid
        clientes={mockClientes}
        total={2}
        loading={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onSearch={onSearch}
        onFilterTipo={vi.fn()}
        onNavigate={vi.fn()}
        search=""
        tipoFilter=""
        canMutate={true}
      />
    )

    const input = screen.getByPlaceholderText('Buscar por nombre, CUIT...')
    fireEvent.change(input, { target: { value: 'Carlos' } })
    expect(onSearch).toHaveBeenCalledWith('Carlos')
  })

  it('triggers tipo filter on select change', () => {
    const onFilterTipo = vi.fn()
    render(
      <ClientesGrid
        clientes={mockClientes}
        total={2}
        loading={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onSearch={vi.fn()}
        onFilterTipo={onFilterTipo}
        onNavigate={vi.fn()}
        search=""
        tipoFilter=""
        canMutate={true}
      />
    )

    const select = screen.getByDisplayValue('Todos')
    fireEvent.change(select, { target: { value: 'mayorista' } })
    expect(onFilterTipo).toHaveBeenCalledWith('mayorista')
  })

  it('shows empty state when no clientes', () => {
    render(
      <ClientesGrid
        clientes={[]}
        total={0}
        loading={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onSearch={vi.fn()}
        onFilterTipo={vi.fn()}
        onNavigate={vi.fn()}
        search=""
        tipoFilter=""
        canMutate={true}
      />
    )

    expect(screen.getByText('No hay clientes')).toBeInTheDocument()
  })

  it('hides edit buttons when canMutate is false', () => {
    render(
      <ClientesGrid
        clientes={mockClientes}
        total={2}
        loading={false}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onSearch={vi.fn()}
        onFilterTipo={vi.fn()}
        onNavigate={vi.fn()}
        search=""
        tipoFilter=""
        canMutate={false}
      />
    )

    expect(screen.queryByText('Editar')).not.toBeInTheDocument()
  })
})
