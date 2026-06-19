import { useState } from 'react'
import type { Producto, CategoriaProducto } from '@/shared/types/producto'

interface ProductoGridProps {
  productos: Producto[]
  categorias: CategoriaProducto[]
  onEdit: (p: Producto) => void
  onToggleActivo: (p: Producto) => void
  onSearch: (q: string) => void
  onFilterCategoria: (id: string) => void
  onFilterActivo: (activo: boolean | undefined) => void
  search: string
  categoriaFilter: string
  activoFilter: boolean | undefined
}

export function ProductoGrid({
  productos,
  categorias,
  onEdit,
  onToggleActivo,
  onSearch,
  onFilterCategoria,
  onFilterActivo,
  search,
  categoriaFilter,
  activoFilter,
}: ProductoGridProps) {
  const [confirmId, setConfirmId] = useState<string | null>(null)

  const getCategoriaNombre = (id: string | null) => {
    if (!id) return '-'
    return categorias.find((c) => c.id === id)?.nombre || '-'
  }

  const getMargenColor = (margen: string) => {
    const m = parseFloat(margen)
    if (m >= 0.4) return 'green'
    if (m >= 0.2) return 'orange'
    return 'red'
  }

  return (
    <div className="producto-grid">
      <div className="filters">
        <input
          placeholder="Buscar por PLU o nombre..."
          value={search}
          onChange={(e) => onSearch(e.target.value)}
        />
        <select value={categoriaFilter} onChange={(e) => onFilterCategoria(e.target.value)}>
          <option value="">Todas las categorías</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>{c.nombre}</option>
          ))}
        </select>
        <select
          value={activoFilter === undefined ? '' : String(activoFilter)}
          onChange={(e) => {
            const v = e.target.value
            onFilterActivo(v === '' ? undefined : v === 'true')
          }}
        >
          <option value="">Todos los estados</option>
          <option value="true">Activos</option>
          <option value="false">Inactivos</option>
        </select>
      </div>

      <table>
        <thead>
          <tr>
            <th>PLU</th>
            <th>Nombre</th>
            <th>Categoría</th>
            <th>Precio Público</th>
            <th>Precio Mayorista</th>
            <th>Costo/kg</th>
            <th>Margen</th>
            <th>Stock</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {productos.map((p) => (
            <tr key={p.id} className={p.activo ? '' : 'inactive'}>
              <td>{p.plu}</td>
              <td>{p.nombre}</td>
              <td>{getCategoriaNombre(p.categoria_id)}</td>
              <td>{p.precio_publico}</td>
              <td>{p.precio_mayorista}</td>
              <td>{p.costo_por_kilo}</td>
              <td style={{ color: getMargenColor(p.margen) }}>
                {(parseFloat(p.margen) * 100).toFixed(2)}%
              </td>
              <td>{p.stock_actual}</td>
              <td>{p.activo ? 'Activo' : 'Inactivo'}</td>
              <td>
                <button onClick={() => onEdit(p)}>Editar</button>
                {confirmId === p.id ? (
                  <>
                    <span>¿Confirmar?</span>
                    <button onClick={() => { onToggleActivo(p); setConfirmId(null) }}>Sí</button>
                    <button onClick={() => setConfirmId(null)}>No</button>
                  </>
                ) : (
                  <button onClick={() => setConfirmId(p.id)}>
                    {p.activo ? 'Desactivar' : 'Activar'}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
