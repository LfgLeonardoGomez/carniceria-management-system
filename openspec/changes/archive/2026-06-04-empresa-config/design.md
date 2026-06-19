# Design: empresa-config (C-03)

## 1. Arquitectura general

```
┌──────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Frontend   │──────│  FastAPI     │──────│  PostgreSQL     │
│  React/Zust. │      │  /empresas/* │      │  (async pg)     │
└──────────────┘      └──────┬───────┘      └─────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐  ┌────▼────┐  ┌──────▼──────┐
        │ Pydantic  │  │  Auth   │  │  Filesystem │
        │ Validators│  │Middleware│  │  UPLOAD_PATH│
        │ (CUIT,   │  │(empresa  │  │  (local)    │
        │  logo)    │  │ _id)     │  │             │
        └───────────┘  └─────────┘  └─────────────┘
```

## 2. Validación de CUIT argentino

### Reglas de formato
- 11 dígitos numéricos exactos.
- Dígito verificador válido según algoritmo AFIP (posiciones 0-9 ponderadas, módulo 11).

### Implementación
- Validador Pydantic a nivel de campo en los request/response schemas.
- Si el CUIT no es válido → `422 Unprocessable Entity` con mensaje claro (`detail: "CUIT inválido"`).
- Se reutiliza el validador tanto en `EmpresaCreate`/`EmpresaUpdate` como en futuros schemas de cliente/proveedor.

```python
def validate_cuit(cuit: str) -> str:
    if not re.fullmatch(r"\d{11}", cuit):
        raise ValueError("CUIT debe contener exactamente 11 dígitos numéricos")
    # Algoritmo dígito verificador AFIP
    base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    digits = [int(d) for d in cuit]
    checksum = sum(b * d for b, d in zip(base, digits[:-1]))
    verifier = (11 - (checksum % 11)) % 11
    if verifier == 10:
        verifier = 0
    if verifier != digits[-1]:
        raise ValueError("Dígito verificador de CUIT inválido")
    return cuit
```

## 3. Estrategia de upload de logo

### Restricciones
- Formatos permitidos: `image/jpeg`, `image/png`. **NO SVG** — las impresoras térmicas de tickets no soportan SVG.
- Tamaño máximo: **2MB** (2 * 1024 * 1024 bytes).
- Validación doble: `python-magic` (MIME type real) + extensión del filename.

### Almacenamiento
- Directorio base: `UPLOAD_PATH` (env var, default `./uploads`).
- Estructura de path: `{UPLOAD_PATH}/empresas/{empresa_id}/logo.{ext}`.
- Nombre de archivo fijo (`logo`) para evitar filenames maliciosos; solo varía la extensión.
- Si ya existe un logo previo, se sobrescribe (soft-overwrite). El anterior se pierde (aceptable para un asset de branding).

### Endpoint
- `POST /empresas/{empresa_id}/logo`
  - Recibe `UploadFile`.
  - Lee `empresa_id` del `request.state.empresa_id` (NO del path param, para evitar que un admin modifique otra empresa).
  - Valida tamaño leyendo chunks (streaming, async).
  - Valida MIME type con `python-magic`.
  - Guarda en filesystem.
  - Actualiza `Empresa.logo_url` con path relativo: `/uploads/empresas/{empresa_id}/logo.{ext}`.
  - Responde con `LogoUploadResponse` (url, filename, content_type).

### Servicio de archivos estáticos
- En dev: FastAPI `StaticFiles` montado en `/uploads` → `UPLOAD_PATH`.
- En prod: se sirve vía nginx/cloudfront; el campo `logo_url` guarda path relativo para ser resuelto por el frontend.

## 4. Estructura de JSON config

Los campos `datos_fiscales`, `configuracion_general`, `parametros_operativos` ya existen en el modelo SQLModel como `JSON`.
Para garantizar type safety y evitar garbage en DB, se define un schema Pydantic por cada campo.

### DatosFiscales (nested en Empresa)
```json
{
  "condicion_iva": "Responsable Inscripto",
  "inicio_actividades": "2015-03-15",
  "punto_venta": 1
}
```
- `condicion_iva`: string (enum opcional en v1.0: Responsable Inscripto, Monotributo, Exento, Consumidor Final).
- `inicio_actividades`: date opcional.
- `punto_venta`: int >= 1.

### ConfiguracionGeneral (nested en Empresa)
```json
{
  "timezone": "America/Argentina/Buenos_Aires",
  "moneda": "ARS",
  "idioma": "es-AR"
}
```
- Placeholder para configuraciones transversales.

### ParametrosOperativos (nested en Empresa)
```json
{
  "alerta_stock_minimo_umbral": 5.0,
  "alerta_gasto_elevado_umbral": 100000.00,
  "alerta_deuda_vencida_dias": 30
}
```
- `alerta_stock_minimo_umbral`: decimal (kg), default 5.0.
- `alerta_gasto_elevado_umbral`: decimal (ARS), default 100000.00.
- `alerta_deuda_vencida_dias`: int, default 30.
- Estos campos son **placeholder** para las notificaciones de US-021; se valida estructura pero no se consume aún.

### Serialización
- SQLModel almacena `dict`; Pydantic valida al crear/actualizar.
- En el router se usa `EmpresaUpdate` con nested models; FastAPI serializa/deserializa automáticamente.

## 5. CRUD endpoints

### GET /empresas/me
- Retorna los datos de la empresa del usuario autenticado.
- Usa `request.state.empresa_id` para filtrar.
- Response: `EmpresaPublic` (todos los campos excepto internals).

### PUT /empresas/me
- Actualiza datos de la empresa.
- Request: `EmpresaUpdate` (todos los campos opcionales; partial update vía PUT/PATCH).
- Valida CUIT si está presente.
- Response: `EmpresaPublic` actualizado.

### PATCH /empresas/me/desactivar
- Soft delete: setea `activa = false`.
- No elimina físicamente (RN-GLOBAL-02).
- Solo Administrador.
- Requiere confirmación (el frontend muestra dialog de confirmación; el backend no tiene lógica adicional, solo setea el flag).

### PATCH /empresas/me/reactivar
- Reactivación: setea `activa = true`.
- Solo Administrador.
- Permite que el admin recupere una empresa desactivada por error sin intervención de soporte.
- Response: `EmpresaPublic` reactivado.

### POST /empresas/me/logo
- Upload de logo (ver sección 3).
- Reemplaza logo existente si lo hay.

> **Nota sobre path param `{empresa_id}`**: En v1.0 un usuario pertenece a una sola empresa. Se usa `/me` en lugar de `/{id}` para evitar enumeración y asegurar que nadie pueda pasar un UUID ajeno. El endpoint ignora cualquier path param y usa `request.state.empresa_id`.

## 6. Seguridad y autorización

### Rol requerido
- Todos los endpoints bajo `/empresas` requieren `rol == "Administrador"`.
- Se crea dependency `require_admin`: extiende `require_auth` y verifica `current_user.rol.nombre == "Administrador"`.
- Si no es admin → `403 Forbidden`.

### Multi-tenant
- `empresa_id` nunca viene del body ni de la URL; siempre de `request.state.empresa_id`.
- Queries a DB: `.where(Empresa.id == request.state.empresa_id)`.
- No se permite que un admin de empresa A consulte/actualice empresa B.

## 7. Modelos Pydantic

```python
class DatosFiscales(BaseModel):
    condicion_iva: str | None = None
    inicio_actividades: date | None = None
    punto_venta: int | None = Field(default=None, ge=1)
    model_config = ConfigDict(extra='forbid')

class ConfiguracionGeneral(BaseModel):
    timezone: str = "America/Argentina/Buenos_Aires"
    moneda: str = "ARS"
    idioma: str = "es-AR"
    model_config = ConfigDict(extra='forbid')

class ParametrosOperativos(BaseModel):
    alerta_stock_minimo_umbral: Decimal = Field(default=Decimal("5.000"), ge=0)
    alerta_gasto_elevado_umbral: Decimal = Field(default=Decimal("100000.00"), ge=0)
    alerta_deuda_vencida_dias: int = Field(default=30, ge=1)
    model_config = ConfigDict(extra='forbid')

class EmpresaUpdate(BaseModel):
    nombre_comercial: str | None = Field(default=None, min_length=1, max_length=255)
    razon_social: str | None = Field(default=None, max_length=255)
    cuit: str | None = None
    domicilio: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    datos_fiscales: DatosFiscales | None = None
    configuracion_general: ConfiguracionGeneral | None = None
    parametros_operativos: ParametrosOperativos | None = None
    model_config = ConfigDict(extra='forbid')

    @field_validator('cuit')
    @classmethod
    def check_cuit(cls, v):
        if v is not None:
            return validate_cuit(v)
        return v

class EmpresaPublic(BaseModel):
    id: UUID
    nombre_comercial: str
    razon_social: str | None
    cuit: str | None
    domicilio: str | None
    telefono: str | None
    email: str | None
    logo_url: str | None
    datos_fiscales: DatosFiscales | None
    configuracion_general: ConfiguracionGeneral | None
    parametros_operativos: ParametrosOperativos | None
    activa: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(extra='forbid')

class LogoUploadResponse(BaseModel):
    logo_url: str
    filename: str
    content_type: str
    model_config = ConfigDict(extra='forbid')
```

## 8. Frontend (React / Zustand)

### Ruta
- `/configuracion/empresa` (protegida por auth + rol admin).

### Componentes
- `EmpresaConfigPage`: layout con formulario.
- `EmpresaForm`: inputs para datos básicos + nested forms para fiscales/config/operativos.
- `LogoUploader`: drag & drop o input file, previsualización de imagen actual, validación de tamaño en frontend (2MB) antes de enviar.
- `DesactivarEmpresaDialog`: confirmación para soft delete.

### State (Zustand)
- `empresaStore`: guarda `EmpresaPublic` del usuario actual.
- `updateEmpresa(dto: EmpresaUpdate)`: PUT a `/empresas/me`.
- `uploadLogo(file: File)`: POST a `/empresas/me/logo`.

### Zero trust
- Validación de CUIT en frontend (UX inmediata) Y backend (seguridad).
- Validación de tamaño de archivo en frontend Y backend.

## 9. Testing strategy

- **Unitarios**: validador de CUIT (casos válidos, inválidos, dígito verificador erróneo, letras, longitud incorrecta).
- **Integración** (pytest + pytest-asyncio + testcontainers PostgreSQL):
  - CRUD completo: GET, PUT con datos fiscales anidados.
  - Validación CUIT: 11 dígitos correcto, dígito verificador incorrecto, 10 dígitos, letras → 422.
  - Upload logo: jpg válido, png válido, svg válido, exe rechazado, 2.1MB rechazado, MIME type spoofing rechazado.
  - Aislamiento: usuario de empresa A no puede leer/escribir empresa B (simulado con empresa_id distinto en JWT).
  - Autorización: usuario no-admin recibe 403 en endpoints /empresas.
  - Soft delete: desactivar empresa, verificar que queda `activa = false`.
- **Coverage**: mínimo 90% del módulo `app/modules/empresa`.

## 10. Decisiones clave

| Decisión | Elección | Justificación |
|----------|----------|---------------|
| Path del endpoint | `/empresas/me` en lugar de `/{id}` | Evita enumeración de IDs y garantiza aislamiento sin confiar en path param. |
| Almacenamiento logo | Filesystem local (`UPLOAD_PATH`) | Simplicidad para dev. Migración a S3 es transparente cambiando el servicio de storage sin tocar la API. |
| Nombre de archivo fijo | `logo.{ext}` | Previene path traversal y filenames maliciosos. |
| JSON config estructurado | Pydantic nested models | Type safety, validación en request/response, evita garbage en DB. |
| Dígito verificador CUIT | Algoritmo AFIP completo | Previene CUIT "casi válidos" que pasarían un regex simple; requisito fiscal argentino. |
