import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
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

function SuperadminRoute({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" />
  if (user?.rol !== 'superadmin') return <Navigate to="/" />
  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" />
  if (user?.rol !== 'admin' && user?.rol !== 'superadmin') return <Navigate to="/" />
  return <>{children}</>
}

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" />
  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <PrivateRoute>
              <DashboardPage />
            </PrivateRoute>
          }
        />
        <Route path="/login" element={<div>Login</div>} />
        <Route
          path="/configuracion/empresa"
          element={
            <AdminRoute>
              <EmpresaConfigPage />
            </AdminRoute>
          }
        />
        <Route
          path="/usuarios"
          element={
            <AdminRoute>
              <UsuariosPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/soporte"
          element={
            <SuperadminRoute>
              <SoportePage />
            </SuperadminRoute>
          }
        />
        <Route
          path="/productos"
          element={
            <PrivateRoute>
              <ProductosPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/clientes"
          element={
            <PrivateRoute>
              <ClientesPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/clientes/:id"
          element={
            <PrivateRoute>
              <ClienteDetailPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/proveedores"
          element={
            <PrivateRoute>
              <ProveedoresPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/proveedores/:id"
          element={
            <PrivateRoute>
              <ProveedorDetailPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/proveedores/:id/editar"
          element={
            <PrivateRoute>
              <ProveedorEditPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/perfil"
          element={
            <PrivateRoute>
              <PerfilPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/compras"
          element={
            <PrivateRoute>
              <ComprasPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/compras/nueva"
          element={
            <PrivateRoute>
              <CompraEditPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/compras/:id"
          element={
            <PrivateRoute>
              <CompraDetailPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/compras/:id/editar"
          element={
            <PrivateRoute>
              <CompraEditPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/despostes"
          element={
            <PrivateRoute>
              <DespostesPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/despostes/nuevo"
          element={
            <PrivateRoute>
              <DesposteNuevoPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/despostes/:id"
          element={
            <PrivateRoute>
              <DesposteDetailPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/stock"
          element={
            <PrivateRoute>
              <StockPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/pos"
          element={
            <PrivateRoute>
              <PosPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/gastos"
          element={
            <PrivateRoute>
              <GastosPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/reportes"
          element={
            <PrivateRoute>
              <ReportesVentasPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/reportes/financieros"
          element={
            <PrivateRoute>
              <ReportesFinancierosPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/rentabilidad"
          element={
            <PrivateRoute>
              <RentabilidadPage />
            </PrivateRoute>
          }
        />
        <Route path="*" element={<div>404</div>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
