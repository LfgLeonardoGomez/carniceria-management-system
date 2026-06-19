import { useState, useCallback, useRef, useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import { useCartStore } from '@/stores/cartStore'
import type { Producto } from '@/shared/types/producto'
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

interface ProductoResumen {
  id: string
  nombre: string
  plu: string
  precio_publico: string
  precio_mayorista: string
  stock_actual: string
}

interface ClienteResumen {
  id: string
  nombre: string
  tipo_cliente: string
}

interface VentaItem {
  producto_id: string
  cantidad_kilos: string
}

interface TicketItem {
  nombre: string
  cantidad_kilos: string
  precio_unitario: string
  importe: string
}

interface TicketData {
  empresa_nombre: string
  fecha: string
  items: TicketItem[]
  subtotal: string
  descuentos: string
  total: string
  medio_de_pago: string
}

const MEDIOS_PAGO = [
  { id: 'efectivo', label: 'Efectivo' },
  { id: 'transferencia', label: 'Transferencia' },
  { id: 'debito', label: 'Débito' },
  { id: 'credito', label: 'Crédito' },
  { id: 'cuenta_corriente', label: 'Cuenta Corriente' },
]

export function PosPage() {
  const { user } = useAuthStore()
  const { items, addItem, removeItem, clearCart } = useCartStore()

  const [pluInput, setPluInput] = useState('')
  const [cantidadInput, setCantidadInput] = useState('1.000')
  const [clienteId, setClienteId] = useState<string | null>(null)
  const [clienteTipo, setClienteTipo] = useState<string>('publico_general')
  const [clientes, setClientes] = useState<ClienteResumen[]>([])
  const [descuentos, setDescuentos] = useState('0.00')
  const [medioPago, setMedioPago] = useState('efectivo')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [ticket, setTicket] = useState<TicketData | null>(null)
  const [ventaId, setVentaId] = useState<string | null>(null)
  const systelRef = useRef<HTMLInputElement>(null)

  const puedeAnular = user?.rol === 'admin' || user?.rol === 'encargado'

  useEffect(() => {
    api.get('/cliente').then((res) => {
      const data = res.data
      if (data?.items) {
        setClientes(data.items)
      }
    }).catch(() => {
      // ignore
    })
  }, [])

  const calcularPrecio = useCallback(
    (producto: ProductoResumen) => {
      if (clienteTipo === 'mayorista') {
        return parseFloat(producto.precio_mayorista)
      }
      return parseFloat(producto.precio_publico)
    },
    [clienteTipo]
  )

  const buscarYAgregarProducto = useCallback(
    async (plu: string, cantidadStr: string) => {
      setError(null)
      try {
        const res = await api.get('/producto', { params: { search: plu } })
        const productos: ProductoResumen[] = res.data?.items || []
        const producto = productos.find((p) => p.plu === plu)
        if (!producto) {
          setError('Producto no encontrado')
          return
        }
        const stock = parseFloat(producto.stock_actual)
        const cantidad = parseFloat(cantidadStr)
        if (cantidad <= 0) {
          setError('La cantidad debe ser mayor a 0')
          return
        }
        if (stock < cantidad) {
          setError(`Stock insuficiente: disponible ${stock.toFixed(3)} kg`)
          return
        }
        const precio = calcularPrecio(producto)
        const importe = precio * cantidad
        addItem({
          producto: producto as unknown as Producto,
          cantidadKg: cantidad,
          subtotal: importe.toFixed(2),
        })
        setPluInput('')
        setCantidadInput('1.000')
      } catch (e: any) {
        setError(e.response?.data?.detail || 'Error al buscar producto')
      }
    },
    [addItem, calcularPrecio]
  )

  const handleAgregar = async () => {
    if (!pluInput.trim()) return
    await buscarYAgregarProducto(pluInput.trim(), cantidadInput)
  }

  const handleSystelInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    if (val.length >= 3) {
      // Simple mock: assume last 3 chars are PLU
      const plu = val.slice(-3)
      buscarYAgregarProducto(plu, cantidadInput)
      e.target.value = ''
    }
  }

  const subtotal = items.reduce((sum, i) => sum + parseFloat(i.subtotal), 0)
  const desc = parseFloat(descuentos) || 0
  const total = Math.max(0, subtotal - desc)

  const buildPayload = (): { cliente_id?: string; items: VentaItem[]; descuentos: string; medio_pago?: string } => ({
    ...(clienteId ? { cliente_id: clienteId } : {}),
    items: items.map((i) => ({
      producto_id: i.producto.id,
      cantidad_kilos: i.cantidadKg.toFixed(3),
    })),
    descuentos: desc.toFixed(2),
    medio_pago: medioPago,
  })

  const crearVenta = async () => {
    if (items.length === 0) {
      setError('Agregá al menos un producto al carrito')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await api.post('/venta', buildPayload())
      setVentaId(res.data.id)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al crear venta')
    } finally {
      setLoading(false)
    }
  }

  const cobrarVenta = async () => {
    if (!ventaId) {
      await crearVenta()
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await api.post(`/venta/${ventaId}/cobrar`, { medio_pago: medioPago })
      setTicket(res.data.ticket)
      clearCart()
      setVentaId(null)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cobrar')
    } finally {
      setLoading(false)
    }
  }

  const suspenderVenta = async () => {
    if (!ventaId) {
      setError('No hay venta activa para suspender')
      return
    }
    setLoading(true)
    try {
      await api.post(`/venta/${ventaId}/suspender`)
      clearCart()
      setVentaId(null)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al suspender')
    } finally {
      setLoading(false)
    }
  }

  const anularVenta = async () => {
    if (!ventaId) {
      setError('No hay venta activa para anular')
      return
    }
    setLoading(true)
    try {
      await api.post(`/venta/${ventaId}/anular`)
      clearCart()
      setVentaId(null)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al anular')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 16, maxWidth: 960, margin: '0 auto' }}>
      <h1>Punto de Venta</h1>

      {/* Campo oculto para SYSTEL */}
      <input
        ref={systelRef}
        type="text"
        style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}
        onChange={handleSystelInput}
        aria-hidden="true"
      />

      {error && (
        <div style={{ color: '#c00', marginBottom: 12, padding: 8, background: '#fee', borderRadius: 4 }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <div>
          <label>Cliente</label>
          <select
            value={clienteId || ''}
            onChange={(e) => {
              const id = e.target.value || null
              setClienteId(id)
              const c = clientes.find((x) => x.id === id)
              setClienteTipo(c?.tipo_cliente || 'publico_general')
            }}
            style={{ width: '100%', padding: 8 }}
          >
            <option value="">Público general</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre} ({c.tipo_cliente})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label>Descuentos ($)</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={descuentos}
            onChange={(e) => setDescuentos(e.target.value)}
            style={{ width: '100%', padding: 8 }}
          />
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          placeholder="PLU"
          value={pluInput}
          onChange={(e) => setPluInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAgregar()}
          style={{ flex: 1, padding: 8 }}
        />
        <input
          placeholder="Cantidad (kg)"
          value={cantidadInput}
          onChange={(e) => setCantidadInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAgregar()}
          style={{ width: 120, padding: 8 }}
        />
        <button onClick={handleAgregar} disabled={loading}>
          Agregar
        </button>
      </div>

      <div style={{ marginBottom: 16 }}>
        <h3>Carrito</h3>
        {items.length === 0 ? (
          <p>Sin ítems</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>Producto</th>
                <th>Cantidad (kg)</th>
                <th style={{ textAlign: 'right' }}>Subtotal</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.producto.id}>
                  <td>{item.producto.nombre}</td>
                  <td style={{ textAlign: 'center' }}>{item.cantidadKg.toFixed(3)}</td>
                  <td style={{ textAlign: 'right' }}>${item.subtotal}</td>
                  <td style={{ textAlign: 'right' }}>
                    <button onClick={() => removeItem(item.producto.id)}>Quitar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div style={{ textAlign: 'right', marginTop: 8 }}>
          <div>Subtotal: ${subtotal.toFixed(2)}</div>
          <div>Descuentos: ${desc.toFixed(2)}</div>
          <div style={{ fontWeight: 'bold', fontSize: 18 }}>Total: ${total.toFixed(2)}</div>
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <h3>Medio de Pago</h3>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {MEDIOS_PAGO.map((m) => (
            <button
              key={m.id}
              onClick={() => setMedioPago(m.id)}
              style={{
                padding: '8px 16px',
                background: medioPago === m.id ? '#007bff' : '#eee',
                color: medioPago === m.id ? '#fff' : '#000',
                border: 'none',
                borderRadius: 4,
                cursor: 'pointer',
              }}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button onClick={cobrarVenta} disabled={loading || items.length === 0}>
          {ventaId ? 'Cobrar' : 'Crear y Cobrar'}
        </button>
        <button onClick={suspenderVenta} disabled={loading || !ventaId}>
          Suspender
        </button>
        {puedeAnular && (
          <button onClick={anularVenta} disabled={loading || !ventaId} style={{ background: '#c00', color: '#fff' }}>
            Anular
          </button>
        )}
      </div>

      {ticket && (
        <div style={{ marginTop: 24, padding: 16, border: '1px solid #ccc', borderRadius: 4, background: '#f9f9f9' }}>
          <h3>Ticket</h3>
          <div><strong>{ticket.empresa_nombre}</strong></div>
          <div>{new Date(ticket.fecha).toLocaleString()}</div>
          <hr />
          <table style={{ width: '100%' }}>
            <tbody>
              {ticket.items.map((it, idx) => (
                <tr key={idx}>
                  <td>{it.nombre}</td>
                  <td>{parseFloat(it.cantidad_kilos).toFixed(3)} kg</td>
                  <td style={{ textAlign: 'right' }}>${parseFloat(it.importe).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <hr />
          <div>Subtotal: ${parseFloat(ticket.subtotal).toFixed(2)}</div>
          <div>Descuentos: ${parseFloat(ticket.descuentos).toFixed(2)}</div>
          <div style={{ fontWeight: 'bold' }}>Total: ${parseFloat(ticket.total).toFixed(2)}</div>
          <div>Medio: {ticket.medio_de_pago}</div>
        </div>
      )}
    </div>
  )
}
