/**
 * EstadoCuentaDownload — button group to download the account statement (C-14, Task 6.6).
 *
 * Props:
 *   clienteId  — customer UUID string
 *
 * TypeScript strict: no `any`.
 */
import { useDescargarEstadoCuenta } from './useCuentasCorrientes'
import type { ExportFormato } from './types'

interface EstadoCuentaDownloadProps {
  clienteId: string
}

export function EstadoCuentaDownload({ clienteId }: EstadoCuentaDownloadProps): JSX.Element {
  const { isDownloading, error, descargar } = useDescargarEstadoCuenta()

  const handleDownload = (formato: ExportFormato) => {
    descargar(clienteId, formato)
  }

  return (
    <div data-testid="estado-cuenta-download">
      <span>Descargar estado de cuenta:</span>
      {(['pdf', 'xlsx', 'csv'] as ExportFormato[]).map((fmt) => (
        <button
          key={fmt}
          onClick={() => handleDownload(fmt)}
          disabled={isDownloading}
          data-testid={`download-${fmt}`}
          style={{ marginLeft: 8 }}
        >
          {fmt.toUpperCase()}
        </button>
      ))}
      {error && (
        <p data-testid="download-error" style={{ color: 'red' }}>
          Error al descargar: {error.message}
        </p>
      )}
    </div>
  )
}
