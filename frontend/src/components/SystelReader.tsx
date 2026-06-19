import { useRef, useEffect, useCallback } from 'react'
import { parseSystelCode, SystelParseError } from '@/utils/systelParser'

export interface SystelReaderProps {
  /** Callback invocado cuando se parsea exitosamente un código SYSTEL. */
  onProductRead: (product: { plu: string; pesoKg: number }) => void
  /** Callback invocado cuando el parseo falla o el código es inválido. */
  onError?: (error: SystelParseError) => void
}

/**
 * Componente que escucha eventos de teclado a través de un input oculto,
 * acumula dígitos numéricos en un buffer interno, y dispara onProductRead
 * cuando detecta un código SYSTEL válido de 13 dígitos.
 *
 * El input está visualmente oculto pero siempre mantiene el foco para
 * capturar la emulación HID del lector de código de barras.
 */
export function SystelReader({ onProductRead, onError }: SystelReaderProps) {
  const bufferRef = useRef<string>('')
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const blurTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clearBuffer = useCallback(() => {
    bufferRef.current = ''
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  const handleParse = useCallback(() => {
    const code = bufferRef.current
    const result = parseSystelCode(code)

    if (result instanceof SystelParseError) {
      onError?.(result)
    } else {
      onProductRead(result)
    }

    clearBuffer()
  }, [onProductRead, onError, clearBuffer])

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      const key = event.key

      // Solo aceptar dígitos 0-9
      if (!/^\d$/.test(key)) {
        return
      }

      // Limpiar timeout previo
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      bufferRef.current += key

      if (bufferRef.current.length >= 13) {
        handleParse()
        return
      }

      // Timeout de 100ms: si no llega nuevo dígito, limpiar buffer
      timeoutRef.current = setTimeout(() => {
        clearBuffer()
      }, 100)
    },
    [handleParse, clearBuffer],
  )

  const handleBlur = useCallback(() => {
    if (blurTimeoutRef.current) {
      clearTimeout(blurTimeoutRef.current)
    }

    blurTimeoutRef.current = setTimeout(() => {
      inputRef.current?.focus()
    }, 50)
  }, [])

  useEffect(() => {
    const input = inputRef.current
    if (!input) return

    input.focus()
    input.addEventListener('keydown', handleKeyDown)
    input.addEventListener('blur', handleBlur)

    return () => {
      input.removeEventListener('keydown', handleKeyDown)
      input.removeEventListener('blur', handleBlur)
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      if (blurTimeoutRef.current) clearTimeout(blurTimeoutRef.current)
    }
  }, [handleKeyDown, handleBlur])

  return (
    <input
      ref={inputRef}
      data-testid="systel-reader-input"
      type="text"
      aria-hidden="true"
      tabIndex={-1}
      style={{
        position: 'absolute',
        opacity: 0,
        width: 0,
        height: 0,
        pointerEvents: 'none',
      }}
      readOnly
    />
  )
}
