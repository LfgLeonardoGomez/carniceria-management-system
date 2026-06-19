## ADDED Requirements

### Requirement: Capturar entrada HID de código de barras
El sistema SHALL escuchar eventos de teclado a través de un input oculto, acumular dígitos numéricos en un buffer interno, y disparar un evento cuando se detecte un código SYSTEL válido.

#### Scenario: Lectura exitosa de 13 dígitos
- **WHEN** el lector de código de barras envía 13 dígitos consecutivos como keystrokes
- **THEN** el componente SHALL acumular los dígitos en el buffer, detectar que alcanzó 13 dígitos, parsear el código, y llamar a `onProductRead` con `{ plu, pesoKg }`
- **AND** el buffer SHALL quedar vacío para la próxima lectura

#### Scenario: Timeout entre dígitos sin alcanzar 13
- **WHEN** se acumulan menos de 13 dígitos y transcurren 100ms sin un nuevo dígito
- **THEN** el componente SHALL limpiar el buffer sin disparar `onProductRead`

#### Scenario: Caracteres no numéricos son ignorados
- **WHEN** se reciben keystrokes que no sean dígitos del `0` al `9`
- **THEN** el componente SHALL ignorarlos y NO agregarlos al buffer

#### Scenario: Foco perdido y recuperado
- **WHEN** el usuario hace click fuera del input oculto y el input pierde el foco
- **THEN** el componente SHALL re-enfocar el input automáticamente dentro de 50ms
- **AND** el buffer SHALL preservarse temporalmente mientras se recupera el foco

#### Scenario: Input oculto no interfere con accesibilidad
- **WHEN** un screen reader navega la página
- **THEN** el input oculto SHALL estar marcado con `aria-hidden="true"` y `tabIndex={-1}`

### Requirement: Exponer API del lector via hook
El sistema SHALL proveer un hook `useSystelReader` que exponga el estado de la lectura y permita pausar/reanudar el lector.

#### Scenario: Hook en modo activo
- **WHEN** el hook se monta con `enabled: true`
- **THEN** el lector SHALL estar activo y escuchando keystrokes

#### Scenario: Pausar y reanudar lector
- **WHEN** el consumidor del hook llama a `pause()`
- **THEN** el lector SHALL dejar de acumular dígitos y limpiar el buffer
- **AND** cuando el consumidor llama a `resume()`
- **THEN** el lector SHALL volver a escuchar keystrokes
