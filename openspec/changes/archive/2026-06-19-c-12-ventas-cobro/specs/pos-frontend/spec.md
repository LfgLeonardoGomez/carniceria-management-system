## ADDED Requirements

### Requirement: Pantalla POS principal
El sistema SHALL proveer una pantalla de caja (POS) que permita agregar productos al carrito, seleccionar cliente, aplicar descuentos, elegir medio de pago y cobrar.

#### Scenario: Agregar producto por PLU
- **WHEN** el cajero escanea o ingresa un PLU válido
- **THEN** el producto se agrega al carrito con cantidad y precio según tipo de cliente

#### Scenario: Carrito visible
- **WHEN** hay ítems en el carrito
- **THEN** la pantalla muestra lista de ítems, subtotal, descuentos y total actualizado

### Requirement: Selección de cliente
El POS SHALL permitir buscar y seleccionar un cliente del listado de la empresa, o vender sin cliente (público general).

#### Scenario: Cliente seleccionado
- **WHEN** el cajero selecciona un cliente mayorista
- **THEN** los precios de los productos en el carrito se actualizan a precio_mayorista

#### Scenario: Sin cliente
- **WHEN** no se selecciona cliente
- **THEN** se usa tipo publico_general y precio_publico

### Requirement: Medios de pago en UI
El POS SHALL mostrar botones o selector para los medios de pago: efectivo, transferencia, débito, crédito, cuenta_corriente.

#### Scenario: Selección de medio
- **WHEN** el cajero selecciona medio efectivo
- **THEN** el sistema prepara el cobro con ese medio

### Requirement: Acciones de cobro y suspensión
El POS SHALL permitir cobrar la venta o suspenderla para recuperarla luego.

#### Scenario: Cobrar venta
- **WHEN** el cajero presiona "Cobrar"
- **THEN** se envía POST /ventas con estado cobrada y se muestra ticket

#### Scenario: Suspender venta
- **WHEN** el cajero presiona "Suspender"
- **THEN** la venta se guarda como suspendida y el carrito se limpia

#### Scenario: Recuperar venta suspendida
- **WHEN** el cajero busca una venta suspendida por ID
- **THEN** el carrito se carga con los datos de esa venta

### Requirement: Anulación desde POS
El POS SHALL permitir anular una venta cobrada, pero solo para usuarios con rol Admin o Encargado.

#### Scenario: Anulación con permisos
- **WHEN** un Admin presiona "Anular" en una venta cobrada
- **THEN** se envía la solicitud de anulación y se confirma

#### Scenario: Anulación sin permisos oculta
- **WHEN** un cajero visualiza una venta cobrada
- **THEN** el botón "Anular" no está visible o está deshabilitado

### Requirement: Estado del lector SYSTEL
El POS SHALL mostrar el estado del lector de balanza SYSTEL (cuando C-11 esté implementado) y un campo oculto para captura rápida.

#### Scenario: Campo oculto de lectura
- **WHEN** el lector SYSTEL emite un código
- **THEN** el campo oculto lo captura sin perder el foco de la UI
- **AND** el producto se agrega al carrito automáticamente
