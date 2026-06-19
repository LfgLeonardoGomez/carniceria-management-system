import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { CompraGrid } from './CompraGrid'

describe('CompraGrid', () => {
  it('renderiza encabezado y botón nueva compra', () => {
    render(
      <BrowserRouter>
        <CompraGrid />
      </BrowserRouter>,
    )
    expect(screen.getByText('Compras de Media Res')).toBeInTheDocument()
    expect(screen.getByText('Nueva Compra')).toBeInTheDocument()
  })

  it('renderiza filtros de fecha y checkbox', () => {
    render(
      <BrowserRouter>
        <CompraGrid />
      </BrowserRouter>,
    )
    expect(screen.getByText('Incluir anuladas')).toBeInTheDocument()
  })
})
