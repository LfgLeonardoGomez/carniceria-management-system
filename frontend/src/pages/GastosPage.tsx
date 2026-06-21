import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useGastoStore } from '@/stores/gastoStore'
import { GastosGrid } from '@/features/gastos/GastosGrid'
import { GastoForm } from '@/features/gastos/GastoForm'
import type { Gasto, GastoCreate, GastoUpdate, CategoriaGasto } from '@/shared/types/gasto'

export function GastosPage() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const {
    gastos,
    totalGastos,
    loading,
    error,
    filters,
    fetchGastos,
    clearError,
  } = useGastoStore()

  const [showForm, setShowForm] = useState(false)
  const [editingGasto, setEditingGasto] = useState<Gasto | null>(null)

  // Admin and Encargado can create/edit/delete gastos
  const canMutate = user?.rol === 'Administrador' || user?.rol === 'Encargado'

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    fetchGastos()
  }, [isAuthenticated, navigate, fetchGastos])

  const handleFilter = (
    categoria: CategoriaGasto | undefined,
    fechaDesde: string,
    fechaHasta: string,
  ) => {
    useGastoStore.getState().setFechaRango(fechaDesde, fechaHasta)
    useGastoStore.getState().setCategoria(categoria)
  }

  const handleSubmit = async (data: GastoCreate | GastoUpdate) => {
    try {
      if (editingGasto) {
        await useGastoStore.getState().updateGasto(editingGasto.id, data as GastoUpdate)
      } else {
        await useGastoStore.getState().createGasto(data as GastoCreate)
      }
      setShowForm(false)
      setEditingGasto(null)
    } catch {
      // error handled in store
    }
  }

  const handleEdit = (gasto: Gasto) => {
    setEditingGasto(gasto)
    setShowForm(true)
  }

  const handleDelete = async (gasto: Gasto) => {
    try {
      await useGastoStore.getState().deleteGasto(gasto.id)
    } catch {
      // error handled in store
    }
  }

  const handleCancelForm = () => {
    setShowForm(false)
    setEditingGasto(null)
  }

  return (
    <div className="gastos-page">
      <h1>Gastos</h1>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={clearError}>×</button>
        </div>
      )}

      {canMutate && !showForm && (
        <div className="actions-bar">
          <button onClick={() => setShowForm(true)}>+ Nuevo Gasto</button>
        </div>
      )}

      {showForm ? (
        <GastoForm
          gasto={editingGasto}
          onSubmit={handleSubmit}
          onCancel={handleCancelForm}
          loading={loading}
          error={error}
        />
      ) : (
        <GastosGrid
          gastos={gastos}
          total={totalGastos}
          loading={loading}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onFilter={handleFilter}
          categoriaActiva={filters.categoria}
          fechaDesde={filters.fecha_desde ?? ''}
          fechaHasta={filters.fecha_hasta ?? ''}
          canMutate={canMutate}
        />
      )}
    </div>
  )
}
