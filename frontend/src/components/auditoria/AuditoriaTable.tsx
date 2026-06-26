import { useAuditoriaStore } from '@/stores/auditoriaStore'
import type { AuditoriaRegistro } from '@/shared/types/auditoria'

interface AuditoriaTableProps {
  /** Resolver nombre legible de un usuario a partir de su id. */
  usuarioNombrePorId?: (id: string) => string | null
}

function formatFechaHora(fecha: string, hora: string): string {
  return `${fecha} ${hora}`
}

function usuarioLabel(
  usuarioId: string | null,
  resolver: AuditoriaTableProps['usuarioNombrePorId'],
): string {
  if (!usuarioId) return 'sistema'
  if (resolver) {
    const nombre = resolver(usuarioId)
    if (nombre) return nombre
  }
  return usuarioId
}

function formatPayload(payload: Record<string, unknown> | null): string {
  if (!payload) return '—'
  try {
    return JSON.stringify(payload, null, 2)
  } catch {
    return '[payload no serializable]'
  }
}

export function AuditoriaTable({ usuarioNombrePorId }: AuditoriaTableProps) {
  const registros = useAuditoriaStore((s) => s.registros)

  if (registros.length === 0) {
    return (
      <div
        className="text-sm text-surface-500 text-center py-8"
        data-testid="auditoria-empty"
      >
        No hay registros de auditoría para los filtros aplicados.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto border border-surface-200 rounded-md">
      <table className="min-w-full text-sm" data-testid="auditoria-table">
        <thead className="bg-surface-50 text-surface-700 text-xs uppercase tracking-wider">
          <tr>
            <th className="text-left px-3 py-2 font-semibold">Fecha y hora</th>
            <th className="text-left px-3 py-2 font-semibold">Usuario</th>
            <th className="text-left px-3 py-2 font-semibold">Acción</th>
            <th className="text-left px-3 py-2 font-semibold">Entidad</th>
            <th className="text-left px-3 py-2 font-semibold">Payload</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-100">
          {registros.map((r: AuditoriaRegistro) => (
            <tr key={r.id} data-testid={`auditoria-row-${r.id}`} className="hover:bg-surface-50">
              <td className="px-3 py-2 text-surface-700 whitespace-nowrap">
                {formatFechaHora(r.fecha, r.hora)}
              </td>
              <td className="px-3 py-2 text-surface-700">
                {usuarioLabel(r.usuario_id, usuarioNombrePorId)}
              </td>
              <td className="px-3 py-2 text-surface-700">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-50 text-primary-700">
                  {r.accion}
                </span>
              </td>
              <td className="px-3 py-2 text-surface-700">
                <div className="flex flex-col">
                  <span className="text-xs uppercase tracking-wide text-surface-500">
                    {r.entidad_tipo}
                  </span>
                  <span className="text-xs text-surface-600 font-mono break-all">
                    {r.entidad_id ?? '—'}
                  </span>
                </div>
              </td>
              <td className="px-3 py-2 text-surface-700">
                <details data-testid={`auditoria-payload-${r.id}`}>
                  <summary className="cursor-pointer text-xs text-primary-600 hover:underline">
                    Ver detalle
                  </summary>
                  <pre className="mt-2 text-xs bg-surface-50 p-2 rounded border border-surface-200 overflow-x-auto max-w-md">
                    {formatPayload(r.payload)}
                  </pre>
                </details>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
