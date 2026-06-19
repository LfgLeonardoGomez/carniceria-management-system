import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LogoUploader } from '@/components/LogoUploader'

describe('LogoUploader', () => {
  it('renders current logo', () => {
    render(<LogoUploader currentLogoUrl="/uploads/logo.jpg" onUpload={vi.fn()} loading={false} />)
    expect(screen.getByAltText('Logo actual')).toBeInTheDocument()
  })

  it('rejects oversized file', () => {
    const onUpload = vi.fn()
    render(<LogoUploader onUpload={onUpload} loading={false} />)

    const input = screen.getByTestId('logo-input')
    const bigFile = new File(['x'], 'logo.jpg', { type: 'image/jpeg' })
    Object.defineProperty(bigFile, 'size', { value: 3 * 1024 * 1024 })

    fireEvent.change(input, { target: { files: [bigFile] } })
    expect(screen.getByText(/excede 2MB/i)).toBeInTheDocument()
    expect(onUpload).not.toHaveBeenCalled()
  })

  it('rejects SVG file', () => {
    const onUpload = vi.fn()
    render(<LogoUploader onUpload={onUpload} loading={false} />)

    const input = screen.getByTestId('logo-input')
    const svgFile = new File(['<svg></svg>'], 'logo.svg', { type: 'image/svg+xml' })

    fireEvent.change(input, { target: { files: [svgFile] } })
    expect(screen.getByText(/Solo se permiten archivos JPG y PNG/i)).toBeInTheDocument()
    expect(onUpload).not.toHaveBeenCalled()
  })

  it('accepts valid PNG file', () => {
    const onUpload = vi.fn().mockResolvedValue(undefined)
    render(<LogoUploader onUpload={onUpload} loading={false} />)

    const input = screen.getByTestId('logo-input')
    const pngFile = new File(['x'], 'logo.png', { type: 'image/png' })
    Object.defineProperty(pngFile, 'size', { value: 1024 })

    fireEvent.change(input, { target: { files: [pngFile] } })
    expect(onUpload).toHaveBeenCalledWith(pngFile)
  })
})
