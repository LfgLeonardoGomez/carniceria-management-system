import { DespostesGrid } from '@/features/despostes/DespostesGrid'
import { DesposteWizard } from '@/features/despostes/DesposteWizard'
import { DesposteDetail } from '@/features/despostes/DesposteDetail'

export function DespostesPage() {
  return <DespostesGrid />
}

export function DesposteNuevoPage() {
  return <DesposteWizard />
}

export function DesposteDetailPage() {
  return <DesposteDetail />
}
