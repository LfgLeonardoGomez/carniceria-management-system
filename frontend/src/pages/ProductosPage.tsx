import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useProductoStore } from '@/stores/productoStore'
import { ProductoGrid } from '@/components/ProductoGrid'
import { ProductoForm } from '@/components/ProductoForm'
import { ImportModal } from '@/components/ImportModal'
import type { Producto } from '@/shared/types/producto'

export function ProductosPage() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const {
    productos,
    categorias,
    loading,
    error,
    importPreview,
    fetchProductos,
    fetchCategorias,
    createProducto,
    updateProducto,
    toggleProductoActivo,
    uploadImport,
    confirmImport,
    clearError,
  } = useProductoStore()

  const [search, setSearch] = useState('')
  const [categoriaFilter, setCategoriaFilter] = useState('')
  const [activoFilter, setActivoFilter] = useState<boolean | undefined>(true)
  const [editingProducto, setEditingProducto] = useState<Producto | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [showImport, setShowImport] = useState(false)

  const canMutate = user?.rol === 'Administrador' || user?.rol === 'Encargado'

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    fetchProductos({ search, categoriaId: categoriaFilter, activo: activoFilter })
    fetchCategorias()
  }, [isAuthenticated, navigate, search, categoriaFilter, activoFilter, fetchProductos, fetchCategorias])

  const handleSearch = useCallback((q: string) => {
    setSearch(q)
  }, [])

  const handleFilterCategoria = useCallback((id: string) => {
    setCategoriaFilter(id)
  }, [])

  const handleFilterActivo = useCallback((activo: boolean | undefined) => {
    setActivoFilter(activo)
  }, [])

  const handleSubmit = async (data: Parameters<typeof createProducto>[0]) => {
    try {
      if (editingProducto) {
        await updateProducto(editingProducto.id, data)
      } else {
        await createProducto(data)
      }
      setShowForm(false)
      setEditingProducto(null)
      fetchProductos({ search, categoriaId: categoriaFilter, activo: activoFilter })
    } catch {
      // error handled in store
    }
  }

  const handleEdit = (p: Producto) => {
    setEditingProducto(p)
    setShowForm(true)
  }

  const handleToggleActivo = async (p: Producto) => {
    try {
      await toggleProductoActivo(p.id, !p.activo)
      fetchProductos({ search, categoriaId: categoriaFilter, activo: activoFilter })
    } catch {
      // error handled in store
    }
  }

  const handleCancelForm = () => {
    setShowForm(false)
    setEditingProducto(null)
  }

  const handleUploadImport = async (file: File) => {
    await uploadImport(file)
  }

  const handleConfirmImport = async (sessionId: string) => {
    const result = await confirmImport(sessionId)
    fetchProductos({ search, categoriaId: categoriaFilter, activo: activoFilter })
    return result
  }

  const handleCloseImport = () => {
    setShowImport(false)
  }

  return (
    <div className="productos-page">
      <h1>Catálogo de Productos</h1>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={clearError}>×</button>
        </div>
      )}

      {canMutate && (
        <div className="actions-bar">
          <button onClick={() => setShowForm(true)}>+ Nuevo Producto</button>
          <button onClick={() => setShowImport(true)}>📥 Importar Excel</button>
        </div>
      )}

      {showForm ? (
        <ProductoForm
          producto={editingProducto}
          categorias={categorias}
          onSubmit={handleSubmit}
          onCancel={handleCancelForm}
          loading={loading}
        />
      ) : (
        <ProductoGrid
          productos={productos}
          categorias={categorias}
          onEdit={handleEdit}
          onToggleActivo={handleToggleActivo}
          onSearch={handleSearch}
          onFilterCategoria={handleFilterCategoria}
          onFilterActivo={handleFilterActivo}
          search={search}
          categoriaFilter={categoriaFilter}
          activoFilter={activoFilter}
        />
      )}

      {showImport && (
        <ImportModal
          preview={importPreview}
          onUpload={handleUploadImport}
          onConfirm={handleConfirmImport}
          onClose={handleCloseImport}
          loading={loading}
        />
      )}
    </div>
  )
}
