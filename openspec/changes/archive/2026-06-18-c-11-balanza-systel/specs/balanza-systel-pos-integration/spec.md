## ADDED Requirements

### Requirement: Integrar lectura SYSTEL con el carrito de ventas
El sistema SHALL, al recibir un código SYSTEL válido, buscar el producto correspondiente por PLU en el backend y agregarlo al carrito del POS con el peso leído.

#### Scenario: Producto encontrado y agregado al carrito
- **WHEN** el lector SYSTEL emite `{ plu: "00027", pesoKg: 4.805 }`
- **AND** el backend responde con el producto PLU 27 (ej. "Bife de Chorizo")
- **THEN** el hook SHALL agregar el producto al carrito con cantidad = 4.805 kg
- **AND** el precio unitario del producto SHALL usarse para calcular el subtotal

#### Scenario: PLU no encontrado en el backend
- **WHEN** el lector SYSTEL emite `{ plu: "99999", pesoKg: 1.5 }`
- **AND** el backend responde con HTTP 404 (PLU no existe)
- **THEN** el sistema SHALL mostrar una notificación de error indicando "Producto no encontrado para el código escaneado"
- **AND** el carrito SHALL permanecer sin cambios
- **AND** el cajero SHALL poder realizar una búsqueda manual del producto

#### Scenario: Error de red al buscar producto
- **WHEN** el lector SYCTEL emite un código válido
- **AND** la llamada al backend falla por error de red (timeout o conexión perdida)
- **THEN** el sistema SHALL mostrar una notificación de error indicando "Error de conexión al buscar el producto"
- **AND** el carrito SHALL permanecer sin cambios

#### Scenario: Lectura múltiple rápida
- **WHEN** el cajero escanea dos productos en rápida sucesión
- **THEN** cada producto SHALL agregarse al carrito secuencialmente sin duplicados ni pérdidas
- **AND** el estado de "procesando" del hook SHALL prevenir agregados concurrentes del mismo código

### Requirement: Calcular subtotal con precisión decimal
El sistema SHALL calcular el subtotal de un ítem pesado usando precisión decimal, nunca punto flotante binario.

#### Scenario: Cálculo de subtotal preciso
- **WHEN** un producto tiene precio_publico = $2499.99 por kg
- **AND** el peso leído es 2.345 kg
- **THEN** el subtotal SHALL ser exactamente $5862.47655 (o redondeado según la regla de negocio del sistema, pero sin errores de punto flotante)
