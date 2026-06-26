import type { ReactNode } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginLayout } from '@/components/layout/LoginLayout'
import { LoginPage } from '@/pages/LoginPage'
import { RecuperarContrasenaPage } from '@/pages/RecuperarContrasenaPage'
import { RestablecerContrasenaPage } from '@/pages/RestablecerContrasenaPage'
import { EmpresaConfigPage } from '@/pages/EmpresaConfigPage'
import { UsuariosPage } from '@/pages/UsuariosPage'
import { PerfilPage } from '@/pages/PerfilPage'
import { ProductosPage } from '@/pages/ProductosPage'
import { ClientesPage, ClienteDetailPage } from '@/pages/ClientesPage'
import { ProveedoresPage, ProveedorDetailPage, ProveedorEditPage } from '@/pages/ProveedoresPage'
import { ComprasPage, CompraDetailPage, CompraEditPage } from '@/pages/ComprasPage'
import { DespostesPage, DesposteNuevoPage, DesposteDetailPage } from '@/pages/DespostesPage'
import { StockPage } from '@/pages/StockPage'
import { SoportePage } from '@/pages/SoportePage'
import { PosPage } from '@/pages/PosPage'
import { GastosPage } from '@/pages/GastosPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ReportesVentasPage } from '@/pages/ReportesVentasPage'
import { ReportesFinancierosPage } from '@/pages/ReportesFinancierosPage'
import { RentabilidadPage } from '@/pages/RentabilidadPage'
import { CuentasCorrientesPage } from '@/pages/CuentasCorrientesPage'
import { AuditoriaPage } from '@/pages/AuditoriaPage'

function SuperadminRoute({ children }: { children: ReactNode }) {
  const { user, isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" />
  if (user?.rol !== 'superadmin') return <Navigate to="/" />
  return <>{children}</>
}

function AdminRoute({ children }: { children: ReactNode }) {
  const { user, isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" />
  if (user?.rol !== 'admin' && user?.rol !== 'superadmin') return <Navigate to="/" />
  return <>{children}</>
}

function PrivateRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" />
  return <>{children}</>
}

function PrivateShell({ children }: { children: ReactNode }) {
  return (
    <PrivateRoute>
      <AppLayout>{children}</AppLayout>
    </PrivateRoute>
  )
}

function PublicShell({ children }: { children: ReactNode }) {
  return <LoginLayout>{children}</LoginLayout>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <PrivateShell>
              <DashboardPage />
            </PrivateShell>
          }
        />
        <Route
          path="/login"
          element={
            <PublicShell>
              <LoginPage />
            </PublicShell>
          }
        />
        <Route
          path="/recuperar-contrasena"
          element={
            <PublicShell>
              <RecuperarContrasenaPage />
            </PublicShell>
          }
        />
        <Route
          path="/restablecer-contrasena"
          element={
            <PublicShell>
              <RestablecerContrasenaPage />
            </PublicShell>
          }
        />
        <Route
          path="/configuracion/empresa"
          element={
            <AdminRoute>
              <AppLayout>
                <EmpresaConfigPage />
              </AppLayout>
            </AdminRoute>
          }
        />
        <Route
          path="/usuarios"
          element={
            <AdminRoute>
              <AppLayout>
                <UsuariosPage />
              </AppLayout>
            </AdminRoute>
          }
        />
        <Route
          path="/admin/soporte"
          element={
            <SuperadminRoute>
              <AppLayout>
                <SoportePage />
              </AppLayout>
            </SuperadminRoute>
          }
        />
        <Route
          path="/productos"
          element={
            <PrivateShell>
              <ProductosPage />
            </PrivateShell>
          }
        />
        <Route
          path="/clientes"
          element={
            <PrivateShell>
              <ClientesPage />
            </PrivateShell>
          }
        />
        <Route
          path="/clientes/:id"
          element={
            <PrivateShell>
              <ClienteDetailPage />
            </PrivateShell>
          }
        />
        <Route
          path="/proveedores"
          element={
            <PrivateShell>
              <ProveedoresPage />
            </PrivateShell>
          }
        />
        <Route
          path="/proveedores/:id"
          element={
            <PrivateShell>
              <ProveedorDetailPage />
            </PrivateShell>
          }
        />
        <Route
          path="/proveedores/:id/editar"
          element={
            <PrivateShell>
              <ProveedorEditPage />
            </PrivateShell>
          }
        />
        <Route
          path="/perfil"
          element={
            <PrivateShell>
              <PerfilPage />
            </PrivateShell>
          }
        />
        <Route
          path="/compras"
          element={
            <PrivateShell>
              <ComprasPage />
            </PrivateShell>
          }
        />
        <Route
          path="/compras/nueva"
          element={
            <PrivateShell>
              <CompraEditPage />
            </PrivateShell>
          }
        />
        <Route
          path="/compras/:id"
          element={
            <PrivateShell>
              <CompraDetailPage />
            </PrivateShell>
          }
        />
        <Route
          path="/compras/:id/editar"
          element={
            <PrivateShell>
              <CompraEditPage />
            </PrivateShell>
          }
        />
        <Route
          path="/despostes"
          element={
            <PrivateShell>
              <DespostesPage />
            </PrivateShell>
          }
        />
        <Route
          path="/despostes/nuevo"
          element={
            <PrivateShell>
              <DesposteNuevoPage />
            </PrivateShell>
          }
        />
        <Route
          path="/despostes/:id"
          element={
            <PrivateShell>
              <DesposteDetailPage />
            </PrivateShell>
          }
        />
        <Route
          path="/stock"
          element={
            <PrivateShell>
              <StockPage />
            </PrivateShell>
          }
        />
        <Route
          path="/pos"
          element={
            <PrivateShell>
              <PosPage />
            </PrivateShell>
          }
        />
        <Route
          path="/gastos"
          element={
            <PrivateShell>
              <GastosPage />
            </PrivateShell>
          }
        />
        <Route
          path="/reportes"
          element={
            <PrivateShell>
              <ReportesVentasPage />
            </PrivateShell>
          }
        />
        <Route
          path="/reportes/financieros"
          element={
            <PrivateShell>
              <ReportesFinancierosPage />
            </PrivateShell>
          }
        />
        <Route
          path="/rentabilidad"
          element={
            <PrivateShell>
              <RentabilidadPage />
            </PrivateShell>
          }
        />
        <Route
          path="/cuentas-corrientes/:clienteId"
          element={
            <PrivateShell>
              <CuentasCorrientesPage />
            </PrivateShell>
          }
        />
        <Route
          path="/auditoria"
          element={
            <AdminRoute>
              <AppLayout>
                <AuditoriaPage />
              </AppLayout>
            </AdminRoute>
          }
        />
        <Route path="*" element={<div>404</div>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
