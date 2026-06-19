## 1. Schema y Seed Data

- [ ] 1.1 Verificar modelo `Usuario` en SQLModel/SQLAlchemy: `id`, `empresa_id`, `email` (unique), `contrasena_hash`, `nombre`, `apellido`, `rol_id` (FK → Rol), `activo`, `ultimo_acceso`, `created_at`, `updated_at`. Asegurar índice compuesto `(empresa_id, activo)`.
- [ ] 1.2 Verificar modelo `Rol` con seed data inicial: Administrador, Encargado, Cajero, Vendedor.
- [ ] 1.3 Verificar seed de usuario administrador por defecto para la empresa de seed (creado en `C-01`), con contraseña hasheada.
- [ ] 1.4 Aplicar Alembic migration si se agrega/modifica constraint de unicidad en `email` o índice compuesto.
- [ ] 1.5 Test de integración: seed data completa (roles + admin) y verificación de índices.

## 2. RBAC Core (Backend)

- [ ] 2.1 Crear `backend/src/common/rbac.py` con matriz de permisos inmutable como diccionario Python: 4 roles × permisos por dominio (ver KB `03_actores_y_roles.md`).
- [ ] 2.2 Crear función `has_permission(rol: str, permiso: str) -> bool` y función `get_permissions(rol: str) -> list[str]`.
- [ ] 2.3 Crear dependency `require_role(permiso: str)` en `backend/src/common/rbac.py` que levante HTTP 403 si el rol no tiene el permiso.
- [ ] 2.4 Extender `get_current_user` en `backend/src/modules/auth/` para que el objeto retornado incluya la lista de `permisos` del usuario según su rol.
- [ ] 2.5 Test de integración: `has_permission` para cada rol con permisos válidos e inválidos.
- [ ] 2.6 Test de integración: `require_role` permite/deniega acceso según matriz.
- [ ] 2.7 Test de integración: `get_current_user` devuelve objeto con `permisos` correctos.

## 3. Servicio de Usuarios (Backend)

- [ ] 3.1 Crear `backend/src/modules/usuario/service.py` con clase `UsuarioService`.
- [ ] 3.2 Implementar `crear_usuario(data: UsuarioCreate, empresa_id: UUID) -> Usuario`: validar email único, validar rol existente, generar contraseña temporal aleatoria (12 chars), hashear con bcrypt, retornar usuario + contraseña temporal (una sola vez).
- [ ] 3.3 Implementar `listar_usuarios(empresa_id: UUID, skip: int, limit: int, activo: bool | None) -> list[Usuario]`: filtrar por empresa y paginar.
- [ ] 3.4 Implementar `obtener_usuario(id: UUID, empresa_id: UUID) -> Usuario`: validar pertenencia a empresa.
- [ ] 3.5 Implementar `actualizar_usuario(id: UUID, empresa_id: UUID, data: UsuarioUpdate) -> Usuario`: validar email único (si cambia), validar rol existente, proteger último admin (no permitir cambio de rol ni desactivación si es el único admin activo).
- [ ] 3.6 Implementar `desactivar_usuario(id: UUID, empresa_id: UUID) -> Usuario`: soft-delete (activo = false), proteger último admin.
- [ ] 3.7 Implementar `reactivar_usuario(id: UUID, empresa_id: UUID) -> Usuario`: activo = true.
- [ ] 3.8 Implementar `obtener_perfil_propio(user_id: UUID) -> Usuario`.
- [ ] 3.9 Implementar `actualizar_perfil_propio(user_id: UUID, data: PerfilUpdate) -> Usuario` y `cambiar_contrasena_propio(user_id: UUID, contrasena_actual: str, contrasena_nueva: str) -> Usuario`.
- [ ] 3.10 Test de integración: CRUD de usuarios con permisos, protección último admin (409), email duplicado (409), login desactivado (401), contraseña temporal generada.
- [ ] 3.11 Test de integración: perfil propio y cambio de contraseña (éxito y fallo por contraseña actual incorrecta).

## 4. Router y Schemas (Backend)

- [ ] 4.1 Crear Pydantic schemas en `backend/src/modules/usuario/schemas.py`: `UsuarioCreate` (extra='forbid'), `UsuarioUpdate` (extra='forbid', todos campos opcionales), `UsuarioPublic` (sin contrasena_hash), `PerfilUpdate`, `CambioContrasena`.
- [ ] 4.2 Crear `backend/src/modules/usuario/router.py` con endpoints:
  - `POST /usuarios` (require_role("usuarios:crear"))
  - `GET /usuarios` (require_role("usuarios:leer"))
  - `GET /usuarios/{id}` (require_role("usuarios:leer"))
  - `PATCH /usuarios/{id}` (require_role("usuarios:actualizar"))
  - `DELETE /usuarios/{id}` (require_role("usuarios:eliminar")) → soft-delete
  - `PATCH /usuarios/{id}/reactivar` (require_role("usuarios:actualizar"))
  - `GET /usuarios/me` (cualquier autenticado)
  - `PATCH /usuarios/me` (cualquier autenticado)
  - `PATCH /usuarios/me/contrasena` (cualquier autenticado)
- [ ] 4.3 Incluir router en `backend/src/main.py` bajo prefix `/usuarios`.
- [ ] 4.4 Test de integración: endpoints responden con códigos correctos, validación extra='forbid' devuelve 422 al enviar campos no esperados.
- [ ] 4.5 Test de integración: respuesta POST `/usuarios` incluye contraseña temporal; GET `/usuarios/{id}` no la incluye.

## 5. Integración con Auth y Protección de Rutas Existentes

- [ ] 5.1 Aplicar `require_role("empresa:crud")` (o permiso equivalente) a endpoints CRUD de `/empresas` en `backend/src/modules/empresa/router.py`.
- [ ] 5.2 Actualizar `POST /auth/login` en `backend/src/modules/auth/router.py` para rechazar login de usuarios con `activo = false` (HTTP 401).
- [ ] 5.3 Test de integración: usuario desactivado no puede loguearse.
- [ ] 5.4 Test de integración: endpoints `/empresas` protegidos (solo Administrador accede, otros roles reciben 403).

## 6. Tests de Integración (Backend)

- [ ] 6.1 Test: login de usuario desactivado → 401.
- [ ] 6.2 Test: CRUD completo de usuarios con permisos (admin crea, lee, actualiza, desactiva, reactiva).
- [ ] 6.3 Test: protección del último administrador → 409 en desactivación y cambio de rol.
- [ ] 6.4 Test: aislamiento multi-tenant (usuario de empresa A no puede ver/Editar usuarios de empresa B).
- [ ] 6.5 Test: email duplicado global → 409 en POST y PATCH.
- [ ] 6.6 Test: `/usuarios/me` retorna datos correctos y permisos del rol.
- [ ] 6.7 Test: cobertura de líneas >= 90% para el módulo `usuario`.
- [ ] 6.8 Test: verificación de que `extra='forbid'` funciona en todos los schemas de request.

## 7. Frontend — Store y Servicios

- [ ] 7.1 Crear Zustand store `frontend/src/stores/usuarioStore.ts` para gestionar listado de usuarios, usuario seleccionado, estados de carga y error.
- [ ] 7.2 Crear servicios API en `frontend/src/services/usuarioService.ts` con funciones para: listar, crear, editar, desactivar, reactivar, obtener perfil, actualizar perfil, cambiar contraseña.
- [ ] 7.3 Test unitario (Vitest): store actualiza correctamente tras mutaciones.

## 8. Frontend — Pantalla de Gestión de Usuarios

- [ ] 8.1 Crear componente `frontend/src/pages/UsuariosPage.tsx` con grid de usuarios (nombre, email, rol, estado, fecha creación) usando paginación.
- [ ] 8.2 Implementar filtros por rol y estado activo en el grid.
- [ ] 8.3 Crear componente `UsuarioForm.tsx` para alta/edición con campos: nombre, apellido, email, rol (selector), activo (checkbox).
- [ ] 8.4 Implementar modal de contraseña temporal que se muestre al crear usuario exitosamente, con botón de copiar al portapapeles. La contraseña no debe persistir en estado después de cerrar el modal.
- [ ] 8.5 Implementar desactivación/reactivación desde el grid con confirmación y manejo de errores (último admin).
- [ ] 8.6 Implementar validación de email duplicado con mensaje de error del backend (409).
- [ ] 8.7 Proteger ruta `/usuarios` en el router: solo accesible para Administrador; redirigir a `/dashboard` si no lo es.
- [ ] 8.8 Test con Playwright (o Vitest + React Testing Library): renderizado del grid, alta con modal, edición, desactivación.

## 9. Frontend — Pantalla de Perfil Propio

- [ ] 9.1 Crear componente `frontend/src/pages/PerfilPage.tsx` con formulario de edición de nombre, apellido y cambio de contraseña.
- [ ] 9.2 Implementar validación de contraseña actual y confirmación de nueva contraseña en el frontend.
- [ ] 9.3 Mostrar mensajes de éxito/error tras operaciones.
- [ ] 9.4 Proteger ruta `/perfil` para cualquier usuario autenticado.
- [ ] 9.5 Test: edición de perfil y cambio de contraseña exitoso/ fallido.

## 10. Documentación y Cierre

- [ ] 10.1 Actualizar `README.md` del backend con endpoints de `/usuarios` y descripción de la matriz RBAC.
- [ ] 10.2 Actualizar `CHANGES.md` del proyecto: marcar `C-04 usuarios-rbac` como `[x]` completado.
- [ ] 10.3 Verificar que todos los archivos placeholder del módulo `usuario` fueron reemplazados por implementación real.
- [ ] 10.4 Ejecutar `pytest` completo y confirmar que no hay regressions en `C-02` ni `C-03`.
- [ ] 10.5 Ejecutar `openspec verify` para confirmar que la implementación cumple specs y tasks.
