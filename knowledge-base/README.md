# BASILE — Base de Conocimiento

Base de conocimiento generada a partir del documento de especificación funcional `docs/BASILE-especificacion.md`.

## Índice de Archivos

| Archivo | Contenido |
|---------|-----------|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito del sistema BASILE, objetivos por actor (Admin, Encargado, Cajero, Vendedor), alcance v1.0, fuera de alcance y métricas de éxito. |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack tecnológico (pendiente de definir), arquitectura general SaaS multi-tenant, integraciones externas (SYSTEL, email, QUENDRA) y propuesta de API REST. |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores del sistema, matriz RBAC completa con permisos CRUD por rol y recurso, y rutas públicas. |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Dominios del sistema, diagrama ERD, entidades detalladas con atributos, relaciones, constraints e índices, y seed data inicial. |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | Reglas de negocio codificadas por dominio (RN-{DOMINIO}-{NN}): seguridad, autenticación, productos, clientes, proveedores, compras, desposte, stock, ventas, caja, medios de pago, cuentas corrientes, gastos, reportes, rentabilidad, auditoría, notificaciones y excepciones globales. |
| [06_funcionalidades.md](06_funcionalidades.md) | 21 historias de usuario (US-001 a US-021) organizadas en 13 épicas: Autenticación, Empresa, Dashboard, Productos, Clientes, Proveedores, Compras/Desposte, Stock, Ventas/Caja, Cuentas Corrientes, Gastos, Reportes/Rentabilidad, Auditoría/Notificaciones. |
| [07_flujos_principales.md](07_flujos_principales.md) | 6 flujos extremo a extremo con disparador, actor, pasos, diagrama ASCII y casos de error: autenticación, venta con balanza SYSTEL, compra de media res, desposte, cierre de caja y recuperación de contraseña. |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones de arquitectura recomendados, estructura de directorios propuesta (frontend + backend), seguridad (auth, autorización, validación, secrets) y tabla de variables de entorno. |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | 5 decisiones de diseño documentadas (DD-01 a DD-05) y 8 supuestos inferidos (SU-01 a SU-08) con riesgos y acciones de validación. |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | 10 inconsistencias detectadas (IN-01 a IN-10) y 12 preguntas abiertas priorizadas con impacto y decisor asignado. |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [10](10_preguntas_abiertas.md)

## Resumen Ejecutivo

BASILE es un SaaS multiempresa y multiusuario para la gestión integral de carnicerías. Su valor diferencial radica en la integración nativa con balanzas SYSTEL (lectura automática de etiquetas), el control de desposte de media res con cálculo de rendimiento y merma, y la centralización financiera (ventas, stock, gastos, caja, rentabilidad) en una única plataforma web responsive. La KB destaca que el stack tecnológico aún no está definido y existen preguntas críticas pendientes (fiscalidad, split de pagos, precios especiales) que deben resolverse antes del Sprint 0.
