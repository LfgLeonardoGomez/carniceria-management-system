# Delta Spec — frontend-layout (c-22)

## ADDED Requirements

### Requirement: Sidebar usa el label "Venta" para la ruta /pos

El sidebar SHALL mostrar el item con `path = "/pos"` con `label = "Venta"` (alineado con la nomenclatura de dominio, no "POS"). El `path` y el componente `PosPage` no cambian.

#### Scenario: Item del POS usa el label "Venta"
- **WHEN** se renderiza el sidebar
- **THEN** el item con `path = "/pos"` muestra el texto "Venta" (no "POS")
- **AND** el `path` sigue siendo `/pos` (no se cambia la ruta)

#### Scenario: Tests del menuConfig siguen pasando
- **WHEN** se ejecuta `frontend/src/components/layout/menuConfig.test.ts`
- **THEN** todas las aserciones pasan (el test no valida labels, solo paths y roles)
