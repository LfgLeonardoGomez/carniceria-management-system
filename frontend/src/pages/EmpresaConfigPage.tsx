import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useEmpresaStore } from '@/stores/empresaStore'
import { EmpresaForm } from '@/components/EmpresaForm'
import { LogoUploader } from '@/components/LogoUploader'

export function EmpresaConfigPage() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const { empresa, loading, error, fetchEmpresa, updateEmpresa, uploadLogo } = useEmpresaStore()

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    if (user?.rol) {
      // In a real app, you'd check the role name; here we rely on backend 403
      fetchEmpresa().catch(() => {})
    }
  }, [isAuthenticated, navigate, user, fetchEmpresa])

  return (
    <div className="empresa-config-page">
      <h1>Configuración de empresa</h1>
      {error && <div className="error">{error}</div>}
      <LogoUploader
        currentLogoUrl={empresa?.logo_url}
        onUpload={uploadLogo}
        loading={loading}
      />
      <EmpresaForm
        empresa={empresa}
        onSubmit={updateEmpresa}
        loading={loading}
      />
    </div>
  )
}
