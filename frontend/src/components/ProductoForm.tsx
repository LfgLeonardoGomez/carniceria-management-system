import { useState, useCallback } from 'react'
import type { Producto, CategoriaProducto } from '@/shared/types/producto'

interface ProductoFormProps {
  producto?: Producto | null
  categorias: CategoriaProducto[]
  onSubmit: (data: {
    plu: string
    nombre: string
    categoria_id: string | null
    precio_publico: string
    precio_mayorista: string
    costo_por_kilo: string
    stock_actual: string
    stock_minimo: string | null
  }) => void
  onCancel: () => void
  loading: boolean
}

export function ProductoForm({ producto, categorias, onSubmit, onCancel, loading }: ProductoFormProps) {
  const [plu, setPlu] = useState(producto?.plu || '')
  const [nombre, setNombre] = useState(producto?.nombre || '')
  const [categoriaId, setCategoriaId] = useState<string>(producto?.categoria_id || '')
  const [precioPublico, setPrecioPublico] = useState(producto?.precio_publico || '')
  const [precioMayorista, setPrecioMayorista] = useState(producto?.precio_mayorista || '')
  const [costoPorKilo, setCostoPorKilo] = useState(producto?.costo_por_kilo || '')
  const [stockActual, setStockActual] = useState(producto?.stock_actual || '')
  const [stockMinimo, setStockMinimo] = useState(producto?.stock_minimo || '')
  const [nuevaCategoria, setNuevaCategoria] = useState('')
  const [showNuevaCategoria, setShowNuevaCategoria] = useState(false)

  const calcularMargen = useCallback(() => {
    const pp = parseFloat(precioPublico)
    const ck = parseFloat(costoPorKilo)
    if (!isNaN(pp) && pp > 0 && !isNaN(ck)) {
      return ((pp - ck) / pp * 100).toFixed(2)
    }
    return '-'
  }, [precioPublico, costoPorKilo])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      plu,
      nombre,
      categoria_id: categoriaId || null,
      precio_publico: precioPublico,
      precio_mayorista: precioMayorista,
      costo_por_kilo: costoPorKilo,
      stock_actual: stockActual,
      stock_minimo: stockMinimo || null,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="producto-form">
      <h2>{producto ? 'Editar Producto' : 'Nuevo Producto'}</h2>

      <div className="form-row">
        <label>PLU</label>
        <input value={plu} onChange={(e) => setPlu(e.target.value)} required maxLength={50} />
      </div>

      <div className="form-row">
        <label>Nombre</label>
        <input value={nombre} onChange={(e) => setNombre(e.target.value)} required maxLength={255} />
      </div>

      <div className="form-row">
        <label>Categoría</label>
        <select value={categoriaId} onChange={(e) => setCategoriaId(e.target.value)}>
          <option value="">Sin categoría</option>
          {categorias.map((c) => (
            <option key={c.id} value={c.id}>{c.nombre}</option>
          ))}
        </select>
        <button type="button" onClick={() => setShowNuevaCategoria((s) => !s)}>
          {showNuevaCategoria ? 'Cancelar' : '+ Nueva'}
        </button>
      </div>

      {showNuevaCategoria && (
        <div className="form-row">
          <label>Nueva categoría</label>
          <input
            value={nuevaCategoria}
            onChange={(e) => setNuevaCategoria(e.target.value)}
            placeholder="Nombre de categoría"
          />
        </div>
      )}

      <div className="form-row">
        <label>Precio Público</label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={precioPublico}
          onChange={(e) => setPrecioPublico(e.target.value)}
          required
        />
      </div>

      <div className="form-row">
        <label>Precio Mayorista</label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={precioMayorista}
          onChange={(e) => setPrecioMayorista(e.target.value)}
          required
        />
      </div>

      <div className="form-row">
        <label>Costo por Kilo</label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={costoPorKilo}
          onChange={(e) => setCostoPorKilo(e.target.value)}
          required
        />
      </div>

      <div className="form-row">
        <label>Stock Actual (kg)</label>
        <input
          type="number"
          step="0.001"
          min="0"
          value={stockActual}
          onChange={(e) => setStockActual(e.target.value)}
          required
        />
      </div>

      <div className="form-row">
        <label>Stock Mínimo (kg)</label>
        <input
          type="number"
          step="0.001"
          min="0"
          value={stockMinimo}
          onChange={(e) => setStockMinimo(e.target.value)}
        />
      </div>

      <div className="form-row">
        <label>Margen estimado</label>
        <span className="margen-preview">{calcularMargen()}%</span>
      </div>

      <div className="form-actions">
        <button type="submit" disabled={loading}>{loading ? 'Guardando...' : 'Guardar'}</button>
        <button type="button" onClick={onCancel}>Cancelar</button>
      </div>
    </form>
  )
}
