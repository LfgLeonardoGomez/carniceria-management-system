import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useClienteStore } from '@/stores/clienteStore'
import { ClientesGrid } from '@/features/clientes/ClientesGrid'
import { ClienteDetail } from '@/features/clientes/ClienteDetail'
import { ClienteForm } from '@/features/clientes/ClienteForm'
import type { ClienteCreate, ClienteUpdate } from '@/shared/types/cliente'

export function ClientesPage() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const {
    clientes,
    totalClientes,
    loading,
    error,
    tipoFilter,
    searchQuery,
    fetchClientes,
    createCliente,
    updateCliente,
    deleteCliente,
    clearError,
  } = useClienteStore()

  const [showForm, setShowForm] = useState(false)
  const [editingCliente, setEditingCliente] = useState<ReturnType<typeof useClienteStore.getState>['clientes'][0] | null>(null)

  const canMutate = user?.rol === 'Administrador' || user?.rol === 'Encargado' || user?.rol === 'Cajero'

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    fetchClientes()
  }, [isAuthenticated, navigate, fetchClientes])

  const handleSearch = (q: string) => {
    useClienteStore.getState().setSearchQuery(q)
  }

  const handleFilterTipo = (tipo: string) => {
    useClienteStore.getState().setTipoFilter(tipo)
  }

  const handleSubmit = async (data: ClienteCreate | ClienteUpdate) => {
    try {
      if (editingCliente) {
        await updateCliente(editingCliente.id, data as ClienteUpdate)
      } else {
        await createCliente(data as ClienteCreate)
      }
      setShowForm(false)
      setEditingCliente(null)
    } catch {
      // error handled in store
    }
  }

  const handleEdit = (cliente: typeof clientes[0]) => {
    setEditingCliente(cliente)
    setShowForm(true)
  }

  const handleDelete = async (cliente: typeof clientes[0]) => {
    try {
      await deleteCliente(cliente.id)
    } catch {
      // error handled in store
    }
  }

  const handleNavigate = (cliente: typeof clientes[0]) => {
    navigate(`/clientes/${cliente.id}`)
  }

  const handleCancelForm = () => {
    setShowForm(false)
    setEditingCliente(null)
  }

  return (
    <div className="clientes-page">
      <h1>Clientes</h1>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={clearError}>×</button>
        </div>
      )}

      {canMutate && !showForm && (
        <div className="actions-bar">
          <button onClick={() => setShowForm(true)}>+ Nuevo Cliente</button>
        </div>
      )}

      {showForm ? (
        <ClienteForm
          cliente={editingCliente}
          onSubmit={handleSubmit}
          onCancel={handleCancelForm}
          loading={loading}
        />
      ) : (
        <ClientesGrid
          clientes={clientes}
          total={totalClientes}
          loading={loading}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onSearch={handleSearch}
          onFilterTipo={handleFilterTipo}
          onNavigate={handleNavigate}
          search={searchQuery}
          tipoFilter={tipoFilter}
          canMutate={canMutate}
        />
      )}
    </div>
  )
}

export function ClienteDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  const {
    selectedCliente,
    historial,
    loading,
    fetchCliente,
    fetchHistorial,
    clearSelected,
  } = useClienteStore()

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    if (id) {
      fetchCliente(id)
      fetchHistorial(id)
    }
  }, [isAuthenticated, navigate, id, fetchCliente, fetchHistorial])

  useEffect(() => {
    return () => {
      clearSelected()
    }
  }, [clearSelected])

  if (!selectedCliente) {
    return <div className="loading">Cargando...</div>
  }

  return (
    <ClienteDetail
      cliente={selectedCliente}
      historial={historial}
      loading={loading}
      onBack={() => navigate('/clientes')}
    />
  )
}
