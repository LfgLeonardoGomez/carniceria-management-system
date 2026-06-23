/**
 * CuentasCorrientesPage — /cuentas-corrientes/:clienteId route (C-14, Task 6.7).
 *
 * Shows:
 *   - Current saldo_actual with Decimal-safe formatting
 *   - Movement history table (HistorialCCTable)
 *   - Payment form (PagoForm) for users with the right permissions
 *   - Downloadable account statement (EstadoCuentaDownload)
 *
 * Role guard: visible to roles that have cuenta-corriente:read / update.
 * TypeScript strict: no `any`.
 */
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { HistorialCCTable } from '@/features/cuentas-corrientes/HistorialCCTable'
import { PagoForm } from '@/features/cuentas-corrientes/PagoForm'
import { EstadoCuentaDownload } from '@/features/cuentas-corrientes/EstadoCuentaDownload'
import { useHistorialCC } from '@/features/cuentas-corrientes/useCuentasCorrientes'

// Roles allowed to read current-account data
const READ_ROLES = ['admin', 'administrador', 'encargado', 'cajero']
// Roles allowed to register payments
const UPDATE_ROLES = ['admin', 'administrador', 'encargado', 'cajero']

export function CuentasCorrientesPage(): JSX.Element {
  const { user } = useAuthStore()
  const { clienteId } = useParams<{ clienteId: string }>()

  if (!user || !READ_ROLES.includes(user.rol)) {
    return (
      <div className="page-container" data-testid="cc-unauthorized">
        <p>No autorizado</p>
      </div>
    )
  }

  if (!clienteId) {
    return (
      <div className="page-container" data-testid="cc-no-cliente">
        <p>Cliente no especificado.</p>
      </div>
    )
  }

  return <CuentasCorrientesContent clienteId={clienteId} canUpdate={UPDATE_ROLES.includes(user.rol)} />
}

interface CuentasCorrientesContentProps {
  clienteId: string
  canUpdate: boolean
}

function CuentasCorrientesContent({ clienteId, canUpdate }: CuentasCorrientesContentProps): JSX.Element {
  const { historial, isLoading, error, refetch } = useHistorialCC(clienteId, 0, 50)
  const [activeTab, setActiveTab] = useState<'historial' | 'pago'>('historial')

  const handlePagoSuccess = (_nuevoSaldo: string) => {
    // Refresh history after payment
    refetch()
    setActiveTab('historial')
  }

  return (
    <div className="page-container cuentas-corrientes-page" data-testid="cc-page">
      <h1>Cuenta Corriente</h1>

      {isLoading && <p data-testid="cc-loading">Cargando...</p>}
      {!isLoading && error && (
        <p data-testid="cc-error" style={{ color: 'red' }}>
          Error al cargar la cuenta corriente.
        </p>
      )}

      {!isLoading && !error && historial && (
        <>
          {/* Balance summary */}
          <div data-testid="cc-saldo-summary" style={{ marginBottom: 16 }}>
            <strong>Saldo actual: </strong>
            <span data-testid="cc-saldo-value">{historial.saldo_actual}</span>
          </div>

          {/* Tab navigation */}
          <nav style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <button
              data-testid="tab-historial"
              aria-selected={activeTab === 'historial'}
              onClick={() => setActiveTab('historial')}
            >
              Historial
            </button>
            {canUpdate && (
              <button
                data-testid="tab-pago"
                aria-selected={activeTab === 'pago'}
                onClick={() => setActiveTab('pago')}
              >
                Registrar pago
              </button>
            )}
          </nav>

          {activeTab === 'historial' && (
            <section data-testid="tab-content-historial">
              <HistorialCCTable
                items={historial.items}
                saldo={historial.saldo_actual}
              />
              <div style={{ marginTop: 16 }}>
                <EstadoCuentaDownload clienteId={clienteId} />
              </div>
            </section>
          )}

          {activeTab === 'pago' && canUpdate && (
            <section data-testid="tab-content-pago">
              <PagoForm clienteId={clienteId} onSuccess={handlePagoSuccess} />
            </section>
          )}
        </>
      )}
    </div>
  )
}
