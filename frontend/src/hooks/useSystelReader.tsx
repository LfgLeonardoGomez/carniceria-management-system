import { useCallback, useRef, useState } from 'react'
import axios from 'axios'
import Decimal from 'decimal.js'
import { SystelReader } from '@/components/SystelReader'
import { useCartStore } from '@/stores/cartStore'
import { SystelParseError } from '@/utils/systelParser'
import { buscarProductoPorPlu } from '@/shared/services/systelService'

export interface UseSystelReaderOptions {
  /** Si el lector está activo y escuchando keystrokes. */
  enabled?: boolean
  /** Callback para errores personalizados (404, red, parseo). */
  onError?: (message: string) => void
}

export interface UseSystelReaderReturn {
  /** Componente SystelReader listo para renderizar. */
  SystelReaderComponent: JSX.Element
  /** Indica si hay una lectura en proceso. */
  isProcessing: boolean
  /** Pausar el lector. */
  pause: () => void
  /** Reanudar el lector. */
  resume: () => void
  /** Estado actual del lector. */
  paused: boolean
}

/**
 * Hook que integra el lector SYSTEL con el carrito de ventas.
 *
 * Al recibir un código SYSTEL válido:
 * 1. Parsea el código para extraer PLU y peso.
 * 2. Consulta el backend via `GET /productos?plu={plu}`.
 * 3. Calcula el subtotal con precisión decimal (Decimal.js).
 * 4. Agrega el producto al carrito Zustand.
 *
 * @example
 * const { SystelReaderComponent, isProcessing, pause, resume } = useSystelReader({ enabled: true })
 * return <div>{SystelReaderComponent}</div>
 */
export function useSystelReader({
  enabled = true,
  onError,
}: UseSystelReaderOptions = {}): UseSystelReaderReturn {
  const [isProcessing, setIsProcessing] = useState(false)
  const [paused, setPaused] = useState(false)
  const processingRef = useRef(false)
  const addItem = useCartStore((state) => state.addItem)

  const handleError = useCallback(
    (message: string) => {
      onError?.(message)
    },
    [onError],
  )

  const handleProductRead = useCallback(
    async ({ plu, pesoKg }: { plu: string; pesoKg: number }) => {
      if (processingRef.current) {
        return
      }

      processingRef.current = true
      setIsProcessing(true)

      try {
        const producto = await buscarProductoPorPlu(plu)

        const precio = new Decimal(producto.precio_publico)
        const peso = new Decimal(pesoKg)
        const subtotal = precio.mul(peso).toFixed(5)

        addItem({
          producto,
          cantidadKg: pesoKg,
          subtotal,
        })
      } catch (err: unknown) {
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          handleError('Producto no encontrado para el código escaneado')
        } else {
          handleError('Error de conexión al buscar el producto')
        }
      } finally {
        processingRef.current = false
        setIsProcessing(false)
      }
    },
    [addItem, handleError],
  )

  const handleParseError = useCallback(
    (error: SystelParseError) => {
      handleError(error.message)
    },
    [handleError],
  )

  const pause = useCallback(() => {
    setPaused(true)
  }, [])

  const resume = useCallback(() => {
    setPaused(false)
  }, [])

  const readerComponent = enabled && !paused ? (
    <SystelReader
      onProductRead={handleProductRead}
      onError={handleParseError}
    />
  ) : null

  return {
    SystelReaderComponent: readerComponent ?? <></>,
    isProcessing,
    pause,
    resume,
    paused,
  }
}
