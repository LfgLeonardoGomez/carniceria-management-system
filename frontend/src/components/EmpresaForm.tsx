import { useState, useEffect } from 'react'
import type { EmpresaPublic, EmpresaUpdate } from '@/shared/types/empresa'
import { validateCuit } from '@/shared/utils/validateCuit'

interface EmpresaFormProps {
  empresa: EmpresaPublic | null
  onSubmit: (dto: EmpresaUpdate) => Promise<void>
  loading: boolean
}

export function EmpresaForm({ empresa, onSubmit, loading }: EmpresaFormProps) {
  const [form, setForm] = useState<EmpresaUpdate>({})
  const [cuitError, setCuitError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)

  useEffect(() => {
    if (empresa) {
      setForm({
        nombre_comercial: empresa.nombre_comercial,
        razon_social: empresa.razon_social || '',
        cuit: empresa.cuit || '',
        domicilio: empresa.domicilio || '',
        telefono: empresa.telefono || '',
        email: empresa.email || '',
        datos_fiscales: empresa.datos_fiscales || { condicion_iva: '', punto_venta: undefined },
        configuracion_general: empresa.configuracion_general || { timezone: 'America/Argentina/Buenos_Aires', moneda: 'ARS', idioma: 'es-AR' },
        parametros_operativos: empresa.parametros_operativos || { alerta_stock_minimo_umbral: '5.000', alerta_gasto_elevado_umbral: '100000.00', alerta_deuda_vencida_dias: 30 },
      })
    }
  }, [empresa])

  const handleChange = (field: keyof EmpresaUpdate, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    if (field === 'cuit') {
      if (value && !validateCuit(value)) {
        setCuitError('CUIT inválido')
      } else {
        setCuitError(null)
      }
    }
  }

  const handleNestedChange = (
    section: 'datos_fiscales' | 'configuracion_general' | 'parametros_operativos',
    field: string,
    value: string | number,
  ) => {
    setForm((prev) => ({
      ...prev,
      [section]: {
        ...(prev[section] || {}),
        [field]: value,
      },
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitError(null)
    if (form.cuit && !validateCuit(form.cuit)) {
      setCuitError('CUIT inválido')
      return
    }
    try {
      const dto: EmpresaUpdate = {
        ...form,
        datos_fiscales: form.datos_fiscales
          ? {
              condicion_iva: form.datos_fiscales.condicion_iva || undefined,
              inicio_actividades: form.datos_fiscales.inicio_actividades || undefined,
              punto_venta: form.datos_fiscales.punto_venta ? Number(form.datos_fiscales.punto_venta) : undefined,
            }
          : undefined,
        configuracion_general: form.configuracion_general || undefined,
        parametros_operativos: form.parametros_operativos
          ? {
              alerta_stock_minimo_umbral: form.parametros_operativos.alerta_stock_minimo_umbral || '5.000',
              alerta_gasto_elevado_umbral: form.parametros_operativos.alerta_gasto_elevado_umbral || '100000.00',
              alerta_deuda_vencida_dias: Number(form.parametros_operativos.alerta_deuda_vencida_dias) || 30,
            }
          : undefined,
      }
      await onSubmit(dto)
    } catch (err: any) {
      setSubmitError(err.response?.data?.detail || 'Error al guardar')
    }
  }

  if (!empresa) return <div>Cargando...</div>

  return (
    <form onSubmit={handleSubmit} className="empresa-form">
      <h2>Datos básicos</h2>
      <div>
        <label>Nombre comercial</label>
        <input
          value={form.nombre_comercial || ''}
          onChange={(e) => handleChange('nombre_comercial', e.target.value)}
          required
        />
      </div>
      <div>
        <label>Razón social</label>
        <input
          value={form.razon_social || ''}
          onChange={(e) => handleChange('razon_social', e.target.value)}
        />
      </div>
      <div>
        <label>CUIT</label>
        <input
          value={form.cuit || ''}
          onChange={(e) => handleChange('cuit', e.target.value)}
          maxLength={11}
        />
        {cuitError && <span className="error">{cuitError}</span>}
      </div>
      <div>
        <label>Domicilio</label>
        <input
          value={form.domicilio || ''}
          onChange={(e) => handleChange('domicilio', e.target.value)}
        />
      </div>
      <div>
        <label>Teléfono</label>
        <input
          value={form.telefono || ''}
          onChange={(e) => handleChange('telefono', e.target.value)}
        />
      </div>
      <div>
        <label>Email</label>
        <input
          type="email"
          value={form.email || ''}
          onChange={(e) => handleChange('email', e.target.value)}
        />
      </div>

      <h2>Datos fiscales</h2>
      <div>
        <label>Condición IVA</label>
        <input
          value={form.datos_fiscales?.condicion_iva || ''}
          onChange={(e) => handleNestedChange('datos_fiscales', 'condicion_iva', e.target.value)}
        />
      </div>
      <div>
        <label>Punto de venta</label>
        <input
          type="number"
          value={form.datos_fiscales?.punto_venta || ''}
          onChange={(e) => handleNestedChange('datos_fiscales', 'punto_venta', e.target.value)}
        />
      </div>

      <h2>Configuración general</h2>
      <div>
        <label>Zona horaria</label>
        <input
          value={form.configuracion_general?.timezone || ''}
          onChange={(e) => handleNestedChange('configuracion_general', 'timezone', e.target.value)}
        />
      </div>
      <div>
        <label>Moneda</label>
        <input
          value={form.configuracion_general?.moneda || ''}
          onChange={(e) => handleNestedChange('configuracion_general', 'moneda', e.target.value)}
        />
      </div>
      <div>
        <label>Idioma</label>
        <input
          value={form.configuracion_general?.idioma || ''}
          onChange={(e) => handleNestedChange('configuracion_general', 'idioma', e.target.value)}
        />
      </div>

      <h2>Parámetros operativos</h2>
      <div>
        <label>Umbral stock mínimo (kg)</label>
        <input
          value={form.parametros_operativos?.alerta_stock_minimo_umbral || ''}
          onChange={(e) => handleNestedChange('parametros_operativos', 'alerta_stock_minimo_umbral', e.target.value)}
        />
      </div>
      <div>
        <label>Umbral gasto elevado ($)</label>
        <input
          value={form.parametros_operativos?.alerta_gasto_elevado_umbral || ''}
          onChange={(e) => handleNestedChange('parametros_operativos', 'alerta_gasto_elevado_umbral', e.target.value)}
        />
      </div>
      <div>
        <label>Días alerta deuda vencida</label>
        <input
          type="number"
          value={form.parametros_operativos?.alerta_deuda_vencida_dias || ''}
          onChange={(e) => handleNestedChange('parametros_operativos', 'alerta_deuda_vencida_dias', e.target.value)}
        />
      </div>

      {submitError && <div className="error">{submitError}</div>}
      <button type="submit" disabled={loading || !!cuitError}>
        {loading ? 'Guardando...' : 'Guardar cambios'}
      </button>
    </form>
  )
}
