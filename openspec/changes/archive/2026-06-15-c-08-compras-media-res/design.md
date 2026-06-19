## Context

BASILE es un SaaS multiempresa para carnicerías. Ya se completaron C-05 (productos-catalogo) y C-07 (proveedores). El modelo de datos ya define la entidad `Compra` en `04_modelo_de_datos.md` y la historia de usuario US-009 en `06_funcionalidades.md` describe el requerimiento. El flujo de compra de media res (Flujo 3) está documentado en `07_flujos_principales.md`.

El backend usa FastAPI + SQLModel + PostgreSQL. El frontend usa React + TypeScript strict + Zustand. Los patrones de C-07 (proveedores) establecen la estructura de routers, servicios, schemas y tests que se replicarán aquí.

## Goals / Non-Goals

**Goals:**
- CRUD completo de compras de media res con validaciones estrictas.
- Cálculo automático de `costo_por_kilo` con precisión decimal (Decimal, no float).
- Entrada automática de stock al crear compra (`MovimientoStock` tipo `entrada_compra`).
- Población del endpoint `GET /proveedores/{id}/historial` con datos reales de compras.
- Soft delete (baja lógica) de compras para preservar historial financiero.
- Frontend con grid, formulario y vista de detalle de compras.
- Tests TDD: tests escritos antes del código productivo.

**Non-Goals:**
- Desposte (C-09): la compra se registra pero el desposte es un change posterior.
- Cálculo de costo promedio histórico complejo: se almacena como snapshot simple en la compra, no como agregación en tiempo real.
- Integración con balanza SYSTEL: no aplica a compras.
- Notificaciones automáticas de compra: fuera de scope.

## Decisions

**1. Usar SQLModel `Compra` con campos Decimal para dinero y peso**
- *Rationale*: RN-COMP-01 exige precisión decimal. SQLModel soporta `Decimal` con `sa_column=Column(Numeric(19,3))`.
- *Alternativa*: Float. Rechazada por pérdida de precisión en cálculos financieros.

**2. Cálculo de `costo_por_kilo` en el servicio, no en el modelo**
- *Rationale*: El modelo almacena el valor calculado pero la lógica de negocio vive en el servicio. Permite testear el cálculo independientemente y reutilizar validaciones.
- *Pattern*: Igual que en C-07 para validaciones de proveedor.

**3. Entrada de stock automática vía `MovimientoStock` con producto genérico "Media Res"**
- *Rationale*: RN-STOCK-02 dice que entradas provienen de compras. Como el desposte (C-09) generará productos específicos, la compra inicial genera stock de un producto genérico o queda disponible para desposte.
- *Implementación*: Se busca o crea un producto con `plu = "MEDIA_RES"` por empresa; si no existe, se crea automáticamente al registrar la primera compra. Esto evita que el usuario tenga que crear el producto manualmente.
- *Alternativa*: No generar stock hasta el desposte. Rechazada porque el kardex debe reflejar entradas (RN-STOCK-05).

**4. Soft delete con campo `estado` (enum: activa, anulada) en lugar de `activo = false`**
- *Rationale*: RN-GLOBAL-01 prohíbe eliminar registros financieros. Una compra "anulada" es más semántico que "inactiva" para este dominio. El historial del proveedor sigue mostrando la compra con estado `anulada`.
- *Pattern*: Similar a baja lógica de proveedor en C-07 pero con semántica de estado específica.

**5. Endpoint de historial en el router de proveedores, servicio en `CompraService`**
- *Rationale*: El endpoint pertenece al dominio de proveedores (`/proveedores/{id}/historial`) pero la query es de compras. El `CompraService` provee el método `get_historial_por_proveedor` que el router de proveedores consume.
- *Pattern*: Cross-domain service call, común en arquitectura por dominio.

**6. Tests con `pytest-asyncio` + `testcontainers` (PostgreSQL real)**
- *Rationale*: Reglas del proyecto — TDD obligatorio, nunca SQLite en tests de integración.
- *Pattern*: Igual que en C-07.

## Risks / Trade-offs

**[Riesgo] División por cero si `peso_total = 0`**
- *Mitigación*: Validación en Pydantic schema (`peso_total > 0`) y doble check en servicio. Frontend también valida antes de enviar.

**[Riesgo] Producto "Media Res" genérico no existe en empresa nueva**
- *Mitigación*: Al crear la primera compra, el servicio crea el producto genérico automáticamente si no existe. Se loggea y se audita.

**[Riesgo] Anulación de compra ya desposteada genera inconsistencia de stock**
- *Mitigación*: En C-08 solo se permite anulación si la compra NO tiene despostes asociados. Validación en servicio: `if compra.despostes: raise HTTPException(409)`. El desposte (C-09) implementará la relación `Compra.despostes`.

**[Riesgo] Costo promedio histórico es un snapshot simple, no un verdadero promedio ponderado**
- *Mitigación*: Aceptado para v1.0. En futuras versiones se puede recalcular con query agregada sobre todas las compras.

**[Trade-off] El servicio de compras crea productos automáticamente**
- *Justificación*: Mejor UX para el usuario. El costo es una responsabilidad extra en el servicio, mitigada con tests específicos.
