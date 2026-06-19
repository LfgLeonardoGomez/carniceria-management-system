# Tasks: empresa-config (C-03)

> TDD obligatorio: cada task con lógica de negocio requiere tests escritos **antes** del código productivo.

---

## Phase 0: Validadores, schemas y utilidades

- [ ] **TASK-0.1** — Crear validador de CUIT argentino en `app/modules/empresa/validators.py`:
  - Función `validate_cuit(cuit: str) -> str`.
  - Regex `^\d{11}$`.
  - Algoritmo AFIP de dígito verificador (ponderación 5-4-3-2-7-6-5-4-3-2, módulo 11).
  - Tests unitarios: CUIT válido (20-12345678-5 ejemplo real), dígito verificador incorrecto, 10 dígitos, 12 dígitos, con letras, string vacío, None.

- [ ] **TASK-0.2** — Crear schemas Pydantic anidados en `app/modules/empresa/schemas.py`:
  - `DatosFiscales`: `condicion_iva` (str, optional), `inicio_actividades` (date, optional), `punto_venta` (int >=1, optional). `extra='forbid'`.
  - `ConfiguracionGeneral`: `timezone` (default "America/Argentina/Buenos_Aires"), `moneda` (default "ARS"), `idioma` (default "es-AR"). `extra='forbid'`.
  - `ParametrosOperativos`: `alerta_stock_minimo_umbral` (Decimal default 5.000 >=0), `alerta_gasto_elevado_umbral` (Decimal default 100000.00 >=0), `alerta_deuda_vencida_dias` (int default 30 >=1). `extra='forbid'`.
  - Tests: instanciación válida, rechazo de campo extra, valores por defecto correctos.

- [ ] **TASK-0.3** — Crear schemas Pydantic de request/response en `app/modules/empresa/schemas.py`:
  - `EmpresaUpdate`: campos opcionales (`nombre_comercial`, `razon_social`, `cuit`, `domicilio`, `telefono`, `email`, `datos_fiscales`, `configuracion_general`, `parametros_operativos`). `extra='forbid'`. Validator `cuit` delega a `validate_cuit`.
  - `EmpresaPublic`: todos los campos de la entidad incluyendo nested models serializados.
  - `LogoUploadResponse`: `logo_url`, `filename`, `content_type`.
  - Tests: serialización/deserialización, validación de CUIT en `EmpresaUpdate`, email inválido rechazado.

- [ ] **TASK-0.4** — Crear servicio de storage de logos en `app/modules/empresa/storage.py`:
  - Función `save_logo(empresa_id: UUID, file: UploadFile, upload_path: Path) -> str`:
    - Lee archivo en chunks async (para no bloquear event loop).
    - Valida tamaño total <= 2MB.
    - Valida MIME type con `python-magic` (image/jpeg, image/png). **Rechaza SVG**.
    - Extrae extensión segura del filename.
    - Guarda en `{upload_path}/empresas/{empresa_id}/logo.{ext}`.
    - Retorna path relativo `/uploads/empresas/{empresa_id}/logo.{ext}`.
  - Función `delete_existing_logo(empresa_id: UUID, upload_path: Path)` para limpiar logo anterior antes de guardar nuevo.
  - Tests unitarios: mock de UploadFile, validación de tamaño, MIME type spoofing, extensión no permitida (incluyendo SVG rechazado).

---

## Phase 1: Dependencias de autorización

- [ ] **TASK-1.1** — Crear dependency `require_admin` en `app/modules/auth/dependencies.py` (o `app/core/dependencies.py`):
  - Extiende `require_auth`.
  - Lee `request.state.current_user`.
  - Verifica `current_user.rol.nombre == "Administrador"`.
  - Si no → `403 Forbidden`.
  - Test de integración: admin pasa, encargado/cajero/vendedor reciben 403.

- [ ] **TASK-1.2** — Verificar que `require_auth` inyecta `empresa_id` en `request.state` (ya de C-02):
  - Tests: endpoint de prueba que lee `request.state.empresa_id` y devuelve 200 si existe.

---

## Phase 2: CRUD backend

- [ ] **TASK-2.1** — Implementar `GET /empresas/me`:
  - Dependency: `require_auth`.
  - Query: `select(Empresa).where(Empresa.id == request.state.empresa_id)`.
  - Response: `EmpresaPublic`.
  - Tests de integración: usuario autenticado recibe sus datos; verificar que nested JSON se serializa correctamente.

- [ ] **TASK-2.2** — Implementar `PUT /empresas/me`:
  - Dependency: `require_admin`.
  - Request: `EmpresaUpdate`.
  - Busca empresa por `request.state.empresa_id`.
  - Aplica update parcial (solo los campos presentes en el DTO).
  - Si `cuit` presente, validar con `validate_cuit` (ya validado por Pydantic, doble chequeo opcional).
  - Commit y refrescar.
  - Response: `EmpresaPublic` actualizado.
  - Tests de integración:
    - Update exitoso de nombre comercial y CUIT.
    - Update parcial (solo teléfono) no borra otros campos.
    - CUIT inválido → 422.
    - Email inválido → 422.
    - Campo extra en JSON anidado → 422 (extra='forbid').

- [ ] **TASK-2.3** — Implementar `PATCH /empresas/me/desactivar`:
  - Dependency: `require_admin`.
  - Busca empresa por `request.state.empresa_id`.
  - Setea `activa = false`.
  - Response: `EmpresaPublic`.
  - Tests: desactivar empresa, verificar `activa = false`; verificar que no es eliminación física (row sigue existiendo).

- [ ] **TASK-2.3b** — Implementar `PATCH /empresas/me/reactivar`:
  - Dependency: `require_admin`.
  - Busca empresa por `request.state.empresa_id`.
  - Setea `activa = true`.
  - Response: `EmpresaPublic`.
  - Tests: reactivar empresa desactivada, verificar `activa = true`; intentar reactivar empresa ya activa (idempotente, no falla).

- [ ] **TASK-2.4** — Implementar `POST /empresas/me/logo`:
  - Dependency: `require_admin`.
  - Recibe `file: UploadFile`.
  - Usa `request.state.empresa_id` (ignora cualquier path param).
  - Delega a `save_logo()`.
  - Actualiza `Empresa.logo_url` en DB.
  - Response: `LogoUploadResponse`.
  - Tests de integración:
    - Subir jpg válido (<=2MB) → 200, logo_url actualizado, archivo existe en filesystem.
    - Subir png válido → 200.
    - Subir svg → 400 (SVG no permitido por impresoras térmicas).
    - Subir exe con extensión renombrada a .jpg → 400 (MIME type spoofing).
    - Subir archivo de 2.1MB → 413 Payload Too Large.
    - Subir bmp → 400 (formato no permitido).

---

## Phase 3: Frontend

- [ ] **TASK-3.1** — Crear página `EmpresaConfigPage` en `frontend/src/pages/EmpresaConfigPage.tsx`:
  - Protegida por auth y rol admin (redirige si no es admin).
  - Layout con tabs o secciones: Datos básicos, Datos fiscales, Configuración general, Parámetros operativos.
  - Tests con Vitest + React Testing Library: render condicional según rol.

- [ ] **TASK-3.2** — Crear componente `EmpresaForm`:
  - Inputs controlados para `nombre_comercial`, `razon_social`, `cuit`, `domicilio`, `telefono`, `email`.
  - Validación de CUIT en tiempo real (regex + dígito verificador con función compartida o duplicada en TS).
  - Inputs anidados para `datos_fiscales`, `configuracion_general`, `parametros_operativos`.
  - Submit hace PUT a `/empresas/me`.
  - Muestra errores de backend (422) en los campos correspondientes.
  - Tests: submit válido, validación CUIT inválido muestra error, campo extra rechazado.

- [ ] **TASK-3.3** — Crear componente `LogoUploader`:
  - Input file con drag & drop.
  - Previsualiza logo actual (desde `EmpresaPublic.logo_url`).
  - Valida tamaño <= 2MB en frontend antes de enviar.
  - Valida extensión (.jpg, .jpeg, .png) en frontend. **No permite SVG**.
  - POST a `/empresas/me/logo`.
  - Actualiza `empresaStore` con nueva `logo_url` tras éxito.
  - Tests: upload exitoso, archivo rechazado por tamaño, previsualización.

- [ ] **TASK-3.4** — Crear store Zustand `empresaStore` en `frontend/src/stores/empresaStore.ts`:
  - Estado: `empresa: EmpresaPublic | null`, `loading`, `error`.
  - Acciones: `fetchEmpresa()`, `updateEmpresa(dto)`, `uploadLogo(file)`.
  - Tests con Vitest: estado después de cada acción, mock de API.

---

## Phase 4: Aislamiento multi-tenant y seguridad

- [ ] **TASK-4.0** — Verificar que el middleware de auth de C-02 rechaza login si `Empresa.activa = false`:
  - En `app/modules/auth/router.py` (login endpoint), después de validar `Usuario.activo = true`, verificar que `Empresa.activa = true`.
  - Si empresa desactivada → `403 Forbidden` con mensaje "Empresa desactivada. Contacte a soporte."
  - Tests: usuario de empresa desactivada intenta login → 403.

- [ ] **TASK-4.1** — Tests de aislamiento:
  - Crear usuario de empresa A y usuario de empresa B en testcontainer.
  - Usuario A autenticado, intenta (forzando empresa_id distinto en JWT mock o simulando URL) → el sistema SIEMPRE usa `request.state.empresa_id` del token válido.
  - Verificar que no hay endpoint que acepte `empresa_id` desde body/URL sin cruzar con el token.
  - Tests de integración: ningún dato de empresa B aparece en respuestas de empresa A.

- [ ] **TASK-4.2** — Verificar que `logo_url` no expone path absoluto del servidor:
  - `logo_url` debe ser relativo (`/uploads/empresas/{id}/logo.jpg`), nunca `/home/user/...`.
  - Test: inspect response de GET /empresas/me.

---

## Phase 5: Integración y validación

- [ ] **TASK-5.1** — Ejecutar suite completa de tests:
  - `pytest tests/integration/test_empresa.py` (o path correspondiente) debe pasar al 100%.
  - Coverage mínimo 90% del módulo `app/modules/empresa`.
  - Vitest tests de frontend deben pasar.

- [ ] **TASK-5.2** — Verificar reglas de negocio:
  - RN-SEG-01: aislamiento total entre empresas.
  - RN-SEG-02: todas las queries filtran por `empresa_id` del usuario autenticado.
  - RN-GLOBAL-02: no hay eliminación física; solo soft delete (`activa = false`).
  - US-003 CA-1: campos obligatorios (nombre comercial, razón social, CUIT, domicilio, teléfono, email) presentes y validados.
  - US-003 CA-2: subir logo funciona.
  - US-003 CA-3: datos fiscales y parámetros operativos configurables.
  - US-003 CA-4: datos visibles en response de empresa (placeholder para reportes/tickets en changes futuros).

- [ ] **TASK-5.3** — Actualizar documentación técnica:
  - Agregar endpoints a Swagger/OpenAPI con descripciones.
  - Documentar path de uploads y restricciones de logo en README de backend.
  - Agregar página de configuración al routing del frontend.

---

## Definición de hecho (DoD)
- [ ] Todos los tests pasan (pytest, pytest-asyncio, testcontainers PostgreSQL; Vitest frontend).
- [ ] Coverage >= 90% en módulo `app/modules/empresa`.
- [ ] Ningún endpoint I/O-bound bloquea el event loop (async/await en todo el pipeline, incluyendo lectura de archivo en chunks).
- [ ] Ningún request/response usa `dict` plano; todo es Pydantic BaseModel con `extra='forbid'`.
- [ ] Validación de CUIT argentino activa en backend (dígito verificador incluido) y frontend.
- [ ] Upload de logo valida MIME type real, extensión permitida y tamaño <= 2MB.
- [ ] Aislamiento multi-tenant verificado: usuario solo accede a datos de su empresa.
- [ ] Soft delete funciona sin eliminación física de registros.
- [ ] Solo usuarios con rol Administrador pueden acceder a endpoints de configuración de empresa.
