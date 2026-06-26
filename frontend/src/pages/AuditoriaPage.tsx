import { useEffect, useState } from 'react'
import { useAuditoriaStore } from '@/stores/auditoriaStore'
import { AuditoriaTable } from '@/components/auditoria/AuditoriaTable'

const ACCIONES_COMUNES = [
  '',
  'CREAR',
  'ACTUALIZAR',
  'ELIMINAR',
  'AJUSTAR',
]

function descargarBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function AuditoriaPage() {
  const registros = useAuditoriaStore((s) => s.registros)
  const total = useAuditoriaStore((s) => s.total)
  const loading = useAuditoriaStore((s) => s.loading)
  const error = useAuditoriaStore((s) => s.error)
  const fetchAuditoria = useAuditoriaStore((s) => s.fetchAuditoria)
  const setFilters = useAuditoriaStore((s) => s.setFilters)
  const exportarCSV = useAuditoriaStore((s) => s.exportarCSV)
  const exportarJSON = useAuditoriaStore((s) => s.exportarJSON)
  const clearError = useAuditoriaStore((s) => s.clearError)

  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')
  const [accion, setAccion] = useState('')
  const [entidadTipo, setEntidadTipo] = useState('')

  useEffect(() => {
    fetchAuditoria()
  }, [fetchAuditoria])

  const handleAplicarFiltros = (e: React.FormEvent) => {
    e.preventDefault()
    setFilters({
      fecha_desde: fechaDesde || undefined,
      fecha_hasta: fechaHasta || undefined,
      accion: accion || undefined,
      entidad_tipo: entidadTipo || undefined,
    })
  }

  const handleLimpiar = () => {
    setFechaDesde('')
    setFechaHasta('')
    setAccion('')
    setEntidadTipo('')
    setFilters({
      fecha_desde: undefined,
      fecha_hasta: undefined,
      accion: undefined,
      entidad_tipo: undefined,
    })
  }

  const handleExportCSV = () => {
    descargarBlob(exportarCSV(), `auditoria-${new Date().toISOString().slice(0, 10)}.csv`)
  }

  const handleExportJSON = () => {
    descargarBlob(exportarJSON(), `auditoria-${new Date().toISOString().slice(0, 10)}.json`)
  }

  return (
    <div className="auditoria-page" data-testid="auditoria-page">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Auditoría</h1>
          <p className="text-sm text-surface-500">
            Historial inmutable de operaciones. Solo accesible para administradores.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleExportCSV}
            disabled={registros.length === 0}
            data-testid="auditoria-export-csv"
            className="px-3 py-2 text-sm font-medium text-surface-700 bg-white border border-surface-300 rounded-md hover:bg-surface-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Exportar CSV
          </button>
          <button
            type="button"
            onClick={handleExportJSON}
            disabled={registros.length === 0}
            data-testid="auditoria-export-json"
            className="px-3 py-2 text-sm font-medium text-surface-700 bg-white border border-surface-300 rounded-md hover:bg-surface-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Exportar JSON
          </button>
        </div>
      </header>

      {error && (
        <div
          role="alert"
          className="mb-4 p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md flex items-center justify-between"
        >
          <span>{error}</span>
          <button type="button" onClick={clearError} className="text-xs underline">
            Cerrar
          </button>
        </div>
      )}

      <form
        onSubmit={handleAplicarFiltros}
        className="mb-4 grid grid-cols-1 md:grid-cols-5 gap-2 p-3 bg-white border border-surface-200 rounded-md"
        data-testid="auditoria-filters"
      >
        <label className="text-sm flex flex-col gap-1">
          <span className="text-surface-700">Fecha desde</span>
          <input
            type="date"
            value={fechaDesde}
            onChange={(e) => setFechaDesde(e.target.value)}
            className="px-2 py-1 border border-surface-300 rounded-md"
            data-testid="auditoria-filter-fecha-desde"
          />
        </label>
        <label className="text-sm flex flex-col gap-1">
          <span className="text-surface-700">Fecha hasta</span>
          <input
            type="date"
            value={fechaHasta}
            onChange={(e) => setFechaHasta(e.target.value)}
            className="px-2 py-1 border border-surface-300 rounded-md"
            data-testid="auditoria-filter-fecha-hasta"
          />
        </label>
        <label className="text-sm flex flex-col gap-1">
          <span className="text-surface-700">Acción</span>
          <select
            value={accion}
            onChange={(e) => setAccion(e.target.value)}
            className="px-2 py-1 border border-surface-300 rounded-md"
            data-testid="auditoria-filter-accion"
          >
            {ACCIONES_COMUNES.map((a) => (
              <option key={a || 'todas'} value={a}>
                {a || 'Todas'}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm flex flex-col gap-1">
          <span className="text-surface-700">Entidad</span>
          <input
            type="text"
            placeholder="cliente, producto, venta…"
            value={entidadTipo}
            onChange={(e) => setEntidadTipo(e.target.value)}
            className="px-2 py-1 border border-surface-300 rounded-md"
            data-testid="auditoria-filter-entidad"
          />
        </label>
        <div className="flex items-end gap-2">
          <button
            type="submit"
            className="px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700"
          >
            Aplicar filtros
          </button>
          <button
            type="button"
            onClick={handleLimpiar}
            className="px-3 py-2 text-sm font-medium text-surface-700 bg-white border border-surface-300 rounded-md hover:bg-surface-50"
          >
            Limpiar
          </button>
        </div>
      </form>

      <p className="text-sm text-surface-500 mb-2" data-testid="auditoria-total">
        {loading ? 'Cargando…' : `${total} ${total === 1 ? 'registro' : 'registros'}`}
      </p>

      <AuditoriaTable />
    </div>
  )
}
