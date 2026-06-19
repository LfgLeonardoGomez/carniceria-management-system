import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useProveedorStore } from '@/stores/proveedorStore'
import { ProveedoresGrid } from '@/features/proveedores/ProveedoresGrid'
import { ProveedorDetail } from '@/features/proveedores/ProveedorDetail'
import { ProveedorForm } from '@/features/proveedores/ProveedorForm'
import type { ProveedorCreate, ProveedorUpdate } from '@/shared/types/proveedor'

export function ProveedoresPage() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const {
    proveedores,
    totalProveedores,
    loading,
    error,
    searchQuery,
    fetchProveedores,
    clearError,
  } = useProveedorStore()

  const [showForm, setShowForm] = useState(false)
  const [editingProveedor, setEditingProveedor] = useState<typeof proveedores[0] | null>(null)

  const canMutate = user?.rol === 'Administrador' || user?.rol === 'Encargado'

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    fetchProveedores()
  }, [isAuthenticated, navigate, fetchProveedores])

  const handleSearch = (q: string) => {
    useProveedorStore.getState().setSearchQuery(q)
  }

  const handleSubmit = async (data: ProveedorCreate | ProveedorUpdate) => {
    try {
      if (editingProveedor) {
        await useProveedorStore.getState().updateProveedor(editingProveedor.id, data as ProveedorUpdate)
      } else {
        await useProveedorStore.getState().createProveedor(data as ProveedorCreate)
      }
      setShowForm(false)
      setEditingProveedor(null)
    } catch {
      // error handled in store
    }
  }

  const handleEdit = (proveedor: typeof proveedores[0]) => {
    setEditingProveedor(proveedor)
    setShowForm(true)
  }

  const handleDelete = async (proveedor: typeof proveedores[0]) => {
    try {
      await useProveedorStore.getState().deleteProveedor(proveedor.id)
    } catch {
      // error handled in store
    }
  }

  const handleNavigate = (proveedor: typeof proveedores[0]) => {
    navigate(`/proveedores/${proveedor.id}`)
  }

  const handleCancelForm = () => {
    setShowForm(false)
    setEditingProveedor(null)
  }

  return (
    <div className="proveedores-page">
      <h1>Proveedores</h1>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={clearError}>×</button>
        </div>
      )}

      {canMutate && !showForm && (
        <div className="actions-bar">
          <button onClick={() => setShowForm(true)}>+ Nuevo Proveedor</button>
        </div>
      )}

      {showForm ? (
        <ProveedorForm
          proveedor={editingProveedor}
          onSubmit={handleSubmit}
          onCancel={handleCancelForm}
          loading={loading}
          error={error}
        />
      ) : (
        <ProveedoresGrid
          proveedores={proveedores}
          total={totalProveedores}
          loading={loading}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onSearch={handleSearch}
          onNavigate={handleNavigate}
          search={searchQuery}
          canMutate={canMutate}
        />
      )}
    </div>
  )
}

export function ProveedorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const {
    selectedProveedor,
    historial,
    loading,
    fetchProveedor,
    fetchHistorial,
    clearSelected,
  } = useProveedorStore()

  const canMutate = user?.rol === 'Administrador' || user?.rol === 'Encargado'

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    if (id) {
      fetchProveedor(id)
      fetchHistorial(id)
    }
  }, [isAuthenticated, navigate, id, fetchProveedor, fetchHistorial])

  useEffect(() => {
    return () => {
      clearSelected()
    }
  }, [clearSelected])

  if (!selectedProveedor && !loading) {
    return <div className="loading">Cargando...</div>
  }

  if (!selectedProveedor) {
    return <div className="loading">Cargando...</div>
  }

  return (
    <ProveedorDetail
      proveedor={selectedProveedor}
      historial={historial}
      loading={loading}
      onBack={() => navigate('/proveedores')}
      onEdit={() => navigate(`/proveedores/${selectedProveedor.id}/editar`)}
      canMutate={canMutate}
    />
  )
}

export function ProveedorEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const {
    selectedProveedor,
    loading,
    error,
    fetchProveedor,
    updateProveedor,
    clearSelected,
  } = useProveedorStore()

  const canMutate = user?.rol === 'Administrador' || user?.rol === 'Encargado'

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    if (!canMutate) {
      navigate('/proveedores')
      return
    }
    if (id) {
      fetchProveedor(id)
    }
  }, [isAuthenticated, navigate, id, fetchProveedor, canMutate])

  useEffect(() => {
    return () => {
      clearSelected()
    }
  }, [clearSelected])

  const handleSubmit = async (data: ProveedorUpdate) => {
    if (!id) return
    try {
      await updateProveedor(id, data)
      navigate('/proveedores')
    } catch {
      // error handled in store
    }
  }

  if (!selectedProveedor && !loading) {
    return <div className="loading">Cargando...</div>
  }

  return (
    <div className="proveedores-page">
      <h1>Editar Proveedor</h1>
      <ProveedorForm
        proveedor={selectedProveedor}
        onSubmit={handleSubmit}
        onCancel={() => navigate('/proveedores')}
        loading={loading}
        error={error}
      />
    </div>
  )
}
