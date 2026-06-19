import { useState, useRef } from 'react'

interface LogoUploaderProps {
  currentLogoUrl?: string
  onUpload: (file: File) => Promise<void>
  loading: boolean
}

const MAX_SIZE = 2 * 1024 * 1024
const ALLOWED_TYPES = ['image/jpeg', 'image/png']
const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png']

export function LogoUploader({ currentLogoUrl, onUpload, loading }: LogoUploaderProps) {
  const [dragActive, setDragActive] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    if (file.size > MAX_SIZE) return 'El archivo excede 2MB'
    if (!ALLOWED_TYPES.includes(file.type)) return 'Solo se permiten archivos JPG y PNG'
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) return 'Extensión no permitida'
    if (file.type === 'image/svg+xml') return 'SVG no permitido'
    return null
  }

  const handleFile = (file: File) => {
    setError(null)
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target?.result as string)
    reader.readAsDataURL(file)
    onUpload(file).catch((err: any) => {
      setError(err.response?.data?.detail || 'Error al subir logo')
    })
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = () => {
    setDragActive(false)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      handleFile(e.target.files[0])
    }
  }

  const imageSrc = preview || currentLogoUrl

  return (
    <div className="logo-uploader">
      <h3>Logo de empresa</h3>
      {imageSrc && (
        <img
          src={imageSrc}
          alt="Logo actual"
          style={{ maxWidth: 200, maxHeight: 200, objectFit: 'contain' }}
        />
      )}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        style={{
          border: dragActive ? '2px dashed #007bff' : '2px dashed #ccc',
          padding: '20px',
          textAlign: 'center',
          cursor: 'pointer',
          marginTop: '10px',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png"
          onChange={handleChange}
          style={{ display: 'none' }}
          data-testid="logo-input"
        />
        <p>Arrastra una imagen aquí o haz clic para seleccionar</p>
        <small>JPG/PNG, máximo 2MB. SVG no permitido.</small>
      </div>
      {loading && <p>Subiendo...</p>}
      {error && <p className="error">{error}</p>}
    </div>
  )
}
