import { useEffect, useMemo, useState } from 'react'
import {
  fetchCajaActual,
  abrirCaja,
  registrarMovimiento,
  cerrarCaja,
} from '@/features/caja/api'
import { calcularDiferencias } from '@/features/caja/calcularDiferencias'
import type {
  CajaActualResponse,
  CierreCajaResponse,
  TipoMovimientoManual,
} from '@/shared/types/caja'

export function CajaPage() {
  const [actual, setActual] = useState<CajaActualResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Apertura
  const [efectivoInicial, setEfectivoInicial] = useState('')

  // Movimiento
  const [movTipo, setMovTipo] = useState<TipoMovimientoManual>('retiro')
  const [movImporte, setMovImporte] = useState('')
  const [movDescripcion, setMovDescripcion] = useState('')

  // Cierre — montos reales contados
  const [efectivoReal, setEfectivoReal] = useState('')
  const [transferenciasReal, setTransferenciasReal] = useState('')
  const [tarjetasReal, setTarjetasReal] = useState('')
  const [resultadoCierre, setResultadoCierre] = useState<CierreCajaResponse | null>(null)

  const cargar = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchCajaActual()
      setActual(data)
    } catch {
      setError('No se pudo cargar el estado de la caja')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void cargar()
  }, [])

  // Live esperado-vs-real comparison (pure, no float — see calcularDiferencias)
  const diferencias = useMemo(() => {
    if (!actual) return null
    return calcularDiferencias(actual.esperado, {
      efectivo: efectivoReal,
      transferencias: transferenciasReal,
      tarjetas: tarjetasReal,
    })
  }, [actual, efectivoReal, transferenciasReal, tarjetasReal])

  const handleAbrir = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await abrirCaja({ efectivo_inicial: efectivoInicial || '0.00' })
      setEfectivoInicial('')
      await cargar()
    } catch {
      setError('No se pudo abrir la caja (¿ya hay una abierta?)')
    }
  }

  const handleMovimiento = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await registrarMovimiento({
        tipo: movTipo,
        importe: movImporte,
        descripcion: movDescripcion || null,
      })
      setMovImporte('')
      setMovDescripcion('')
      await cargar()
    } catch {
      setError('No se pudo registrar el movimiento')
    }
  }

  const handleCerrar = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      const res = await cerrarCaja({
        efectivo_real: efectivoReal || '0.00',
        transferencias_real: transferenciasReal || '0.00',
        tarjetas_real: tarjetasReal || '0.00',
      })
      setResultadoCierre(res)
      await cargar()
    } catch {
      setError('No se pudo cerrar la caja')
    }
  }

  if (loading) return <div className="caja-page">Cargando…</div>

  return (
    <div className="caja-page">
      <h1>Caja</h1>
      {error && <div role="alert" className="caja-error">{error}</div>}

      {!actual && !resultadoCierre && (
        <section className="caja-apertura">
          <h2>Apertura de caja</h2>
          <form onSubmit={handleAbrir}>
            <label>
              Efectivo inicial
              <input
                type="number"
                step="0.01"
                min="0"
                value={efectivoInicial}
                onChange={(ev) => setEfectivoInicial(ev.target.value)}
                placeholder="0.00"
              />
            </label>
            <button type="submit">Abrir caja</button>
          </form>
        </section>
      )}

      {actual && (
        <>
          <section className="caja-movimientos">
            <h2>Movimientos manuales</h2>
            <form onSubmit={handleMovimiento}>
              <select
                value={movTipo}
                onChange={(ev) => setMovTipo(ev.target.value as TipoMovimientoManual)}
                aria-label="Tipo de movimiento"
              >
                <option value="retiro">Retiro</option>
                <option value="ingreso_manual">Ingreso manual</option>
              </select>
              <input
                type="number"
                step="0.01"
                min="0"
                value={movImporte}
                onChange={(ev) => setMovImporte(ev.target.value)}
                placeholder="Importe"
                aria-label="Importe del movimiento"
              />
              <input
                type="text"
                value={movDescripcion}
                onChange={(ev) => setMovDescripcion(ev.target.value)}
                placeholder="Descripción"
                aria-label="Descripción del movimiento"
              />
              <button type="submit">Registrar</button>
            </form>
          </section>

          <section className="caja-cierre">
            <h2>Cierre de caja</h2>
            <table className="caja-comparacion">
              <thead>
                <tr>
                  <th>Medio</th>
                  <th>Esperado</th>
                  <th>Real (contado)</th>
                  <th>Diferencia</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Efectivo</td>
                  <td>{actual.esperado.efectivo}</td>
                  <td>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={efectivoReal}
                      onChange={(ev) => setEfectivoReal(ev.target.value)}
                      aria-label="Efectivo real"
                    />
                  </td>
                  <td>{diferencias?.diferenciaEfectivo ?? '0.00'}</td>
                </tr>
                <tr>
                  <td>Transferencias</td>
                  <td>{actual.esperado.transferencias}</td>
                  <td>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={transferenciasReal}
                      onChange={(ev) => setTransferenciasReal(ev.target.value)}
                      aria-label="Transferencias reales"
                    />
                  </td>
                  <td>{diferencias?.diferenciaTransferencias ?? '0.00'}</td>
                </tr>
                <tr>
                  <td>Tarjetas</td>
                  <td>{actual.esperado.tarjetas}</td>
                  <td>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={tarjetasReal}
                      onChange={(ev) => setTarjetasReal(ev.target.value)}
                      aria-label="Tarjetas reales"
                    />
                  </td>
                  <td>{diferencias?.diferenciaTarjetas ?? '0.00'}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={3}>Diferencia total</td>
                  <td
                    className={
                      diferencias?.tieneDiferencia ? 'caja-diferencia-alerta' : ''
                    }
                  >
                    {diferencias?.diferenciaTotal ?? '0.00'}
                  </td>
                </tr>
              </tfoot>
            </table>
            <form onSubmit={handleCerrar}>
              <button type="submit">Confirmar cierre</button>
            </form>
          </section>
        </>
      )}

      {resultadoCierre && (
        <section className="caja-resumen">
          <h2>Resumen de cierre</h2>
          <p>
            Diferencia total: <strong>{resultadoCierre.diferencias.diferencia_total}</strong>
          </p>
          {resultadoCierre.diferencias.diferencia_significativa && (
            <p role="alert" className="caja-diferencia-alerta">
              Se detectó una diferencia significativa en el cierre.
            </p>
          )}
        </section>
      )}
    </div>
  )
}
