import { CompraGrid } from '@/features/compras/CompraGrid'
import { CompraForm } from '@/features/compras/CompraForm'
import { CompraDetail } from '@/features/compras/CompraDetail'

export function ComprasPage() {
  return (
    <div className="p-6">
      <CompraGrid />
    </div>
  )
}

export function CompraDetailPage() {
  return (
    <div className="p-6">
      <CompraDetail />
    </div>
  )
}

export function CompraEditPage() {
  return (
    <div className="p-6">
      <CompraForm />
    </div>
  )
}
