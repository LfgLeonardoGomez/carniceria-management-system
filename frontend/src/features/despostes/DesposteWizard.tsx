import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDesposteStore } from '@/stores/desposteStore'
import { useCompraStore } from '@/stores/compraStore'
import { useProductoStore } from '@/stores/productoStore'
import { TIPOS_CORTE } from '@/shared/types/desposte'

export function DesposteWizard() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [saving, setSaving] = useState(false)

  const {
    wizardData,
    setWizardData,
    setCorteWizard,
    createDesposte,
    addCorte,
    finalizarDesposte,
    error,
    clearError,
  } = useDesposteStore()

  const { compras, fetchCompras } = useCompraStore()
  const { productos, fetchProductos } = useProductoStore()

  // Load compras and productos on mount
  useMemo(() => {
    fetchCompras()
    fetchProductos()
  }, [])

  const compraSeleccionada = useMemo(() => {
    return compras.find((c) => c.id === wizardData.compraId)
  }, [compras, wizardData.compraId])

  const pesoTotalCompra = useMemo(() => {
    return parseFloat(compraSeleccionada?.peso_total ?? '0')
  }, [compraSeleccionada])

  const costoTotalCompra = useMemo(() => {
    return parseFloat(compraSeleccionada?.costo_total ?? '0')
  }, [compraSeleccionada])

  const rendimientoTotal = useMemo(() => {
    let total = 0
    wizardData.cortes.forEach((c) => {
      const k = parseFloat(c.kilos)
      if (!isNaN(k) && k > 0) total += k
    })
    return total
  }, [wizardData.cortes])

  const merma = useMemo(() => {
    return Math.max(0, pesoTotalCompra - rendimientoTotal)
  }, [pesoTotalCompra, rendimientoTotal])

  const excedePeso = rendimientoTotal > pesoTotalCompra
  const cercaLimite = pesoTotalCompra > 0 && rendimientoTotal >= pesoTotalCompra * 0.95 && !excedePeso

  const handleCrearDesposte = async () => {
    if (!wizardData.compraId || !wizardData.operadorId) return
    setSaving(true)
    try {
      const desposte = await createDesposte({
        compra_id: wizardData.compraId,
        fecha: wizardData.fecha,
        operador_id: wizardData.operadorId,
      })
      setStep(2)
      return desposte
    } catch {
      // error handled in store
    } finally {
      setSaving(false)
    }
  }

  const handleAgregarCortes = async (desposteId: string) => {
    setSaving(true)
    try {
      for (const [tipo, data] of wizardData.cortes.entries()) {
        const kilos = parseFloat(data.kilos)
        if (!isNaN(kilos) && kilos > 0) {
          await addCorte(desposteId, {
            tipo_corte: tipo,
            kilos_obtenidos: data.kilos,
            producto_id: data.productoId,
          })
        }
      }
      setStep(3)
    } catch {
      // error handled in store
    } finally {
      setSaving(false)
    }
  }

  const handleFinalizar = async (desposteId: string) => {
    setSaving(true)
    try {
      await finalizarDesposte(desposteId)
      navigate('/despostes')
    } catch {
      // error handled in store
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h2 className="text-xl font-bold mb-4">Nuevo Desposte — Paso {step} de 3</h2>
      {error && (
        <div className="mb-4 p-2 bg-red-100 text-red-700 rounded">
          {error}
          <button className="ml-2 text-sm underline" onClick={clearError}>
            Cerrar
          </button>
        </div>
      )}

      {/* Paso 1: Seleccionar compra, fecha, operador */}
      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="block font-medium mb-1">Compra de Media Res</label>
            <select
              className="w-full border p-2 rounded"
              value={wizardData.compraId}
              onChange={(e) => setWizardData({ compraId: e.target.value })}
            >
              <option value="">Seleccionar compra...</option>
              {compras.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.fecha} — {c.proveedor?.nombre ?? 'Proveedor'} — {c.peso_total} kg — ${c.costo_total}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-medium mb-1">Fecha del Desposte</label>
            <input
              type="date"
              className="w-full border p-2 rounded"
              value={wizardData.fecha}
              onChange={(e) => setWizardData({ fecha: e.target.value })}
            />
          </div>

          <div>
            <label className="block font-medium mb-1">Operador</label>
            <select
              className="w-full border p-2 rounded"
              value={wizardData.operadorId}
              onChange={(e) => setWizardData({ operadorId: e.target.value })}
            >
              <option value="">Seleccionar operador...</option>
              {/* In a real app, fetch usuarios from a store */}
              <option value="operador-1">Operador 1</option>
            </select>
          </div>

          <button
            className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
            disabled={!wizardData.compraId || !wizardData.operadorId || saving}
            onClick={handleCrearDesposte}
          >
            {saving ? 'Creando...' : 'Continuar'}
          </button>
        </div>
      )}

      {/* Paso 2: Tabla de cortes */}
      {step === 2 && compraSeleccionada && (
        <div>
          <div className="mb-4 p-3 bg-gray-50 rounded">
            <p className="font-medium">Compra seleccionada:</p>
            <p className="text-sm text-gray-600">
              {compraSeleccionada.proveedor?.nombre} — Peso total: {compraSeleccionada.peso_total} kg — Costo total: ${compraSeleccionada.costo_total}
            </p>
          </div>

          {/* Resumen en vivo */}
          <div className={`mb-4 p-3 rounded ${excedePeso ? 'bg-red-100 text-red-800' : cercaLimite ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-50 text-blue-800'}`}>
            <div className="flex gap-6 flex-wrap">
              <div>
                <span className="text-sm">Rendimiento total:</span>
                <span className="font-bold ml-1">{rendimientoTotal.toFixed(3)} kg</span>
              </div>
              <div>
                <span className="text-sm">Merma:</span>
                <span className="font-bold ml-1">{merma.toFixed(3)} kg</span>
              </div>
              <div>
                <span className="text-sm">% Rendimiento:</span>
                <span className="font-bold ml-1">
                  {pesoTotalCompra > 0 ? ((rendimientoTotal / pesoTotalCompra) * 100).toFixed(1) : 0}%
                </span>
              </div>
              {excedePeso && (
                <div className="font-bold text-red-700">
                  ⚠️ El rendimiento supera el peso de la compra
                </div>
              )}
              {cercaLimite && (
                <div className="font-bold text-yellow-700">
                  ⚠️ Estás cerca del límite de peso
                </div>
              )}
            </div>
          </div>

          <table className="w-full border mb-4">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-2 border text-left">Corte</th>
                <th className="p-2 border text-right">Kilos</th>
                <th className="p-2 border text-right">% Rend.</th>
                <th className="p-2 border text-right">Costo Asignado</th>
                <th className="p-2 border text-right">Costo/kg</th>
                <th className="p-2 border text-left">Producto</th>
              </tr>
            </thead>
            <tbody>
              {TIPOS_CORTE.map((tipo) => {
                const data = wizardData.cortes.get(tipo)
                const kilos = parseFloat(data?.kilos ?? '0')
                const porcentaje = pesoTotalCompra > 0 && kilos > 0 ? (kilos / pesoTotalCompra) * 100 : 0
                const costoAsignado = pesoTotalCompra > 0 && kilos > 0 ? (costoTotalCompra / pesoTotalCompra) * kilos : 0
                const costoKg = kilos > 0 ? costoAsignado / kilos : 0
                return (
                  <tr key={tipo}>
                    <td className="p-2 border capitalize">{tipo.replace('_', ' ')}</td>
                    <td className="p-2 border">
                      <input
                        type="number"
                        step="0.001"
                        className="w-full text-right border p-1 rounded"
                        value={data?.kilos ?? ''}
                        onChange={(e) => setCorteWizard(tipo, e.target.value, data?.productoId ?? null)}
                        placeholder="0.000"
                      />
                    </td>
                    <td className="p-2 border text-right">
                      {kilos > 0 ? `${porcentaje.toFixed(1)}%` : '—'}
                    </td>
                    <td className="p-2 border text-right">
                      {kilos > 0 ? `$${costoAsignado.toFixed(2)}` : '—'}
                    </td>
                    <td className="p-2 border text-right">
                      {kilos > 0 ? `$${costoKg.toFixed(2)}` : '—'}
                    </td>
                    <td className="p-2 border">
                      <select
                        className="w-full border p-1 rounded"
                        value={data?.productoId ?? ''}
                        onChange={(e) =>
                          setCorteWizard(tipo, data?.kilos ?? '', e.target.value || null)
                        }
                      >
                        <option value="">Sin producto</option>
                        {productos.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.nombre} (PLU: {p.plu})
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          <div className="flex gap-3">
            <button
              className="px-4 py-2 bg-gray-200 rounded"
              onClick={() => setStep(1)}
            >
              Volver
            </button>
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
              disabled={excedePeso || rendimientoTotal === 0 || saving}
              onClick={() => {
                // In a real app, we need the desposte ID from step 1.
                // For simplicity, the wizard would store it.
                // Here we use a placeholder approach.
                const desposteId = useDesposteStore.getState().selectedDesposte?.id
                if (desposteId) handleAgregarCortes(desposteId)
              }}
            >
              {saving ? 'Guardando...' : 'Continuar al resumen'}
            </button>
          </div>
        </div>
      )}

      {/* Paso 3: Resumen y finalizar */}
      {step === 3 && (
        <div>
          <h3 className="text-lg font-bold mb-3">Resumen del Desposte</h3>
          <div className="p-4 bg-gray-50 rounded mb-4">
            <p>Rendimiento total: {rendimientoTotal.toFixed(3)} kg</p>
            <p>Merma: {merma.toFixed(3)} kg</p>
            <p>Cortes registrados: {wizardData.cortes.size}</p>
          </div>
          <div className="flex gap-3">
            <button
              className="px-4 py-2 bg-gray-200 rounded"
              onClick={() => setStep(2)}
            >
              Volver
            </button>
            <button
              className="px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50"
              disabled={saving}
              onClick={() => {
                const desposteId = useDesposteStore.getState().selectedDesposte?.id
                if (desposteId) handleFinalizar(desposteId)
              }}
            >
              {saving ? 'Finalizando...' : 'Finalizar Desposte'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
