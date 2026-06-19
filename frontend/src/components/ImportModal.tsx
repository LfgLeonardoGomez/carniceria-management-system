import { useState, useRef } from 'react'
import type { ImportPreview, ImportConfirmResult } from '@/shared/types/producto'

interface ImportModalProps {
  preview: ImportPreview | null
  onUpload: (file: File) => Promise<void>
  onConfirm: (sessionId: string) => Promise<ImportConfirmResult>
  onClose: () => void
  loading: boolean
}

export function ImportModal({ preview, onUpload, onConfirm, onClose, loading }: ImportModalProps) {
  const [_file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<ImportConfirmResult | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const dropped = e.dataTransfer.files[0]
    if (dropped && dropped.name.endsWith('.xlsx')) {
      setFile(dropped)
      onUpload(dropped)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected) {
      setFile(selected)
      onUpload(selected)
    }
  }

  const handleConfirm = async () => {
    if (!preview?.session_id) return
    const res = await onConfirm(preview.session_id)
    setResult(res)
  }

  const handleClose = () => {
    setFile(null)
    setResult(null)
    onClose()
  }

  return (
    <div className="import-modal-overlay" onClick={handleClose}>
      <div className="import-modal" onClick={(e) => e.stopPropagation()}>
        <h2>Importar productos desde Excel QUENDRA</h2>
        <button className="close-btn" onClick={handleClose}>×</button>

        {!preview && !result && (
          <div
            className="drop-zone"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
          >
            <p>Arrastrá un archivo .xlsx acá o hacé clic para seleccionar</p>
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx"
              onChange={handleFileChange}
              hidden
            />
          </div>
        )}

        {loading && <p className="loading">Procesando...</p>}

        {preview && !result && (
          <div className="preview">
            <p>Filas válidas: {preview.validas_count} | Inválidas: {preview.invalidas_count}</p>

            {preview.filas_validas.length > 0 && (
              <>
                <h3>Válidas</h3>
                <table>
                  <thead>
                    <tr><th>Fila</th><th>PLU</th><th>Nombre</th><th>Categoría</th><th>Precio</th></tr>
                  </thead>
                  <tbody>
                    {preview.filas_validas.map((f) => (
                      <tr key={f.row_num}>
                        <td>{f.row_num}</td>
                        <td>{f.plu}</td>
                        <td>{f.nombre}</td>
                        <td>{f.categoria}</td>
                        <td>{f.precio_publico}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}

            {preview.filas_invalidas.length > 0 && (
              <>
                <h3>Inválidas</h3>
                <table>
                  <thead>
                    <tr><th>Fila</th><th>PLU</th><th>Nombre</th><th>Errores</th></tr>
                  </thead>
                  <tbody>
                    {preview.filas_invalidas.map((f) => (
                      <tr key={f.row_num} className="invalid-row">
                        <td>{f.row_num}</td>
                        <td>{f.plu}</td>
                        <td>{f.nombre}</td>
                        <td>{f.errores?.join(', ')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}

            <div className="modal-actions">
              <button onClick={handleConfirm} disabled={loading || preview.validas_count === 0}>
                {loading ? 'Importando...' : 'Confirmar importación'}
              </button>
              <button onClick={handleClose}>Cancelar</button>
            </div>
          </div>
        )}

        {result && (
          <div className="import-result">
            <h3>Importación completada</h3>
            <p>Productos creados: {result.creados}</p>
            <p>Errores: {result.errores}</p>
            <button onClick={handleClose}>Cerrar</button>
          </div>
        )}
      </div>
    </div>
  )
}
