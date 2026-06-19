import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useUsuarioStore } from '@/stores/usuarioStore'
import { UsuarioCreateModal } from '@/components/UsuarioCreateModal'
import { UsuarioEditModal } from '@/components/UsuarioEditModal'
import { ROLES } from '@/shared/types/usuario'
import type { UsuarioPublic, UsuarioUpdate } from '@/shared/types/usuario'

export function UsuariosPage() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const {
    usuarios,
    total,
    loading,
    error,
    tempPassword,
    skip,
    limit,
    activoFilter,
    rolFilter,
    fetchUsuarios,
    createUsuario,
    updateUsuario,
    deactivateUsuario,
    reactivateUsuario,
    clearTempPassword,
    clearError,
  } = useUsuarioStore()

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showConfirmDeactivate, setShowConfirmDeactivate] = useState(false)
  const [showTempPasswordModal, setShowTempPasswordModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState<UsuarioPublic | null>(null)
  const [lastAdminError, setLastAdminError] = useState(false)
  const [editSuccess, setEditSuccess] = useState(false)

  const isAdmin = user?.rol === 'Administrador'

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    if (!isAdmin) {
      navigate('/')
      return
    }
    fetchUsuarios(skip, limit, activoFilter, rolFilter).catch(() => {})
  }, [isAuthenticated, isAdmin, navigate])

  useEffect(() => {
    if (tempPassword) {
      setShowTempPasswordModal(true)
    }
  }, [tempPassword])

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => clearError(), 8000)
      return () => clearTimeout(timer)
    }
  }, [error, clearError])

  const handleCreate = async (dto: Parameters<typeof createUsuario>[0]) => {
    try {
      await createUsuario(dto)
      setShowCreateModal(false)
      fetchUsuarios(0, limit, activoFilter, rolFilter).catch(() => {})
    } catch (err: unknown) {
      // error ya está en el store
    }
  }

  const handleEdit = async (dto: UsuarioUpdate) => {
    if (!selectedUser) return
    try {
      await updateUsuario(selectedUser.id, dto)
      setShowEditModal(false)
      setSelectedUser(null)
      setEditSuccess(true)
      setTimeout(() => setEditSuccess(false), 4000)
      fetchUsuarios(skip, limit, activoFilter, rolFilter).catch(() => {})
    } catch (err: unknown) {
      // error ya está en el store
    }
  }

  const handleDeactivate = async () => {
    if (!selectedUser) return
    try {
      await deactivateUsuario(selectedUser.id)
      setShowConfirmDeactivate(false)
      setSelectedUser(null)
      setLastAdminError(false)
      fetchUsuarios(skip, limit, activoFilter, rolFilter).catch(() => {})
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status?: number } }
      if (axiosErr.response?.status === 409) {
        setLastAdminError(true)
      }
    }
  }

  const handleReactivate = async (id: string) => {
    try {
      await reactivateUsuario(id)
      fetchUsuarios(skip, limit, activoFilter, rolFilter).catch(() => {})
    } catch {
      // error ya está en el store
    }
  }

  const openEditModal = (u: UsuarioPublic) => {
    setSelectedUser(u)
    setShowEditModal(true)
    clearError()
  }

  const openDeactivateConfirm = (u: UsuarioPublic) => {
    setSelectedUser(u)
    setLastAdminError(false)
    setShowConfirmDeactivate(true)
  }

  const closeTempPasswordModal = () => {
    setShowTempPasswordModal(false)
    clearTempPassword()
  }

  const totalPages = Math.ceil(total / limit)
  const currentPage = Math.floor(skip / limit)

  if (!isAdmin) {
    return <div>Redirigiendo...</div>
  }

  return (
    <div className="usuarios-page">
      <h1>Gestión de usuarios</h1>

      {error && <div className="error-banner" role="alert">{error}</div>}
      {editSuccess && (
        <div className="success-banner" role="status">
          Usuario actualizado correctamente
        </div>
      )}

      <div className="toolbar">
        <button onClick={() => { setShowCreateModal(true); clearError() }} disabled={loading}>
          + Nuevo usuario
        </button>
        <div className="filters">
          <label htmlFor="filtro-estado">Estado:</label>
          <select
            id="filtro-estado"
            value={activoFilter === null ? '' : String(activoFilter)}
            onChange={(e) => {
              const val = e.target.value
              fetchUsuarios(0, limit, val === '' ? null : val === 'true', rolFilter).catch(() => {})
            }}
          >
            <option value="">Todos</option>
            <option value="true">Activos</option>
            <option value="false">Inactivos</option>
          </select>
          <label htmlFor="filtro-rol">Rol:</label>
          <select
            id="filtro-rol"
            value={rolFilter || ''}
            onChange={(e) => {
              const val = e.target.value
              fetchUsuarios(0, limit, activoFilter, val || null).catch(() => {})
            }}
          >
            <option value="">Todos</option>
            {ROLES.map((r) => (
              <option key={r.id} value={r.nombre}>
                {r.nombre}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && <div className="loading">Cargando...</div>}

      <table className="usuarios-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Email</th>
            <th>Rol</th>
            <th>Estado</th>
            <th>Fecha creación</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {usuarios.map((u) => (
            <tr key={u.id} className={u.activo ? '' : 'inactive'}>
              <td>{[u.nombre, u.apellido].filter(Boolean).join(' ') || '-'}</td>
              <td>{u.email}</td>
              <td>{u.rol || '-'}</td>
              <td>{u.activo ? 'Activo' : 'Inactivo'}</td>
              <td>{new Date(u.created_at).toLocaleDateString('es-AR')}</td>
              <td>
                <button onClick={() => openEditModal(u)}>Editar</button>
                {u.activo ? (
                  <button onClick={() => openDeactivateConfirm(u)}>Desactivar</button>
                ) : (
                  <button onClick={() => handleReactivate(u.id)}>Reactivar</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button
          disabled={currentPage === 0}
          onClick={() => fetchUsuarios(skip - limit, limit, activoFilter, rolFilter).catch(() => {})}
        >
          Anterior
        </button>
        <span>
          Página {currentPage + 1} de {totalPages || 1} ({total} total)
        </span>
        <button
          disabled={currentPage + 1 >= totalPages}
          onClick={() => fetchUsuarios(skip + limit, limit, activoFilter, rolFilter).catch(() => {})}
        >
          Siguiente
        </button>
      </div>

      {showCreateModal && (
        <UsuarioCreateModal
          onSubmit={handleCreate}
          onCancel={() => setShowCreateModal(false)}
          loading={loading}
          error={error}
        />
      )}

      {showEditModal && selectedUser && (
        <UsuarioEditModal
          usuario={selectedUser}
          onSubmit={handleEdit}
          onCancel={() => { setShowEditModal(false); setSelectedUser(null); clearError() }}
          loading={loading}
          error={error}
        />
      )}

      {showConfirmDeactivate && selectedUser && (
        <div className="modal-overlay" onClick={() => setShowConfirmDeactivate(false)} role="dialog" aria-modal="true">
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Confirmar desactivación</h2>
            <p>
              ¿Desactivar a <strong>{selectedUser.email}</strong>?
            </p>
            {lastAdminError && (
              <p className="warning" role="alert">
                No se puede desactivar al único administrador activo de la empresa.
              </p>
            )}
            <div className="modal-actions">
              <button onClick={handleDeactivate} disabled={loading || lastAdminError}>
                Desactivar
              </button>
              <button onClick={() => setShowConfirmDeactivate(false)}>Cancelar</button>
            </div>
          </div>
        </div>
      )}

      {showTempPasswordModal && tempPassword && (
        <div className="modal-overlay" onClick={closeTempPasswordModal} role="dialog" aria-modal="true">
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Usuario creado</h2>
            <p>Compartí esta contraseña temporal con el usuario. No se volverá a mostrar.</p>
            <div className="temp-password-box">
              <code>{tempPassword}</code>
              <button
                onClick={() => navigator.clipboard.writeText(tempPassword)}
                type="button"
              >
                Copiar
              </button>
            </div>
            <div className="modal-actions">
              <button onClick={closeTempPasswordModal}>Cerrar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
